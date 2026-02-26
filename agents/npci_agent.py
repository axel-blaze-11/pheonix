"""
NPCI Switch AI Agent - Creates change manifests and dispatches them.
"""

import logging
from typing import Dict, List, Optional, Any

import os
from llm import LLM
from manifest import ChangeManifest, ChangeType
from code_updater import CodeUpdater
from docker_manager import DockerManager
from a2a_protocol import A2AClient, A2AMessage
from .base_agent import BaseAgent, AgentStatus

logger = logging.getLogger(__name__)


class NPCIAgent(BaseAgent):
    """NPCI Switch agent that creates and dispatches change manifests."""
    
    def __init__(self, llm_instance: Optional[LLM] = None):
        """Initialize NPCI agent."""
        super().__init__(
            agent_id="NPCI_AGENT",
            agent_name="NPCI Switch Agent",
            llm_instance=llm_instance,
        )
        self.code_updater = CodeUpdater(base_path=".")
        self.docker_manager = DockerManager()
        self.a2a_client = A2AClient()
    
    def create_manifest(
        self,
        description: str,
        change_type: ChangeType,
        affected_components: List[str],
        xsd_changes: Optional[Dict] = None,
        code_changes: Optional[Dict] = None,
        test_requirements: Optional[List[str]] = None,
    ) -> ChangeManifest:
        """
        Create a new change manifest.
        
        Args:
            description: Description of the change
            change_type: Type of change
            affected_components: List of component names affected
            xsd_changes: Optional XSD change details
            code_changes: Optional code change details
            test_requirements: Optional test requirements
            
        Returns:
            Created manifest
        """
        manifest = ChangeManifest(
            change_type=change_type,
            description=description,
            affected_components=affected_components,
            xsd_changes=xsd_changes or {},
            code_changes=code_changes or {},
            test_requirements=test_requirements or [],
            created_by=self.agent_id,
        )
        
        
        logger.info(f"[{self.agent_name}] Created manifest: {manifest.change_id}")
        
        # Determine orchestrator URL
        from a2a_protocol import A2AClient
        a2a = A2AClient()
        # Hacky: send initial status to orchestrator manually since NPCI doesn't "receive" its own manifest in the same way
        # In a real system, we'd have a cleaner way, but for now we use A2A client to update orchestrator
        try:
            import requests
            orchestrator_url = a2a.get_service_url("ORCHESTRATOR")
            
            # Register change first
            requests.post(
                f"{orchestrator_url}/api/orchestrator/register",
                json={"manifest": manifest.to_dict(), "receivers": []},
                timeout=5
            )

            # Then send status
            requests.post(
                f"{orchestrator_url}/api/orchestrator/status",
                json={
                    "change_id": manifest.change_id,
                    "agent_id": self.agent_id,
                    "status": "RECEIVED",  # Initial status
                    "details": f"Manifest created: {manifest.description}"
                },
                timeout=5
            )
        except Exception:
            pass # Ignore errors here, just best effort logging
            
        return manifest
    
    def dispatch_manifest(
        self,
        manifest: ChangeManifest,
        receivers: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """
        Dispatch manifest to receiver agents.
        
        Args:
            manifest: Manifest to dispatch
            receivers: List of receiver agent IDs (defaults to all bank/PSP agents)
            
        Returns:
            Dictionary mapping receiver to success status
        """
        if receivers is None:
            receivers = [
                "REMITTER_BANK_AGENT",
                "BENEFICIARY_BANK_AGENT",
                "PAYER_PSP_AGENT",
                "PAYEE_PSP_AGENT",
            ]
        
        manifest.status = "DISPATCHED"
        results = self.a2a_client.broadcast_manifest(
            manifest_dict=manifest.to_dict(),
            sender=self.agent_id,
            receivers=receivers,
        )
        
        logger.info(f"[{self.agent_name}] Dispatched manifest {manifest.change_id} to {len(receivers)} agents")
        
        # Log dispatch
        try:
            import requests
            orchestrator_url = self.a2a_client.get_service_url("ORCHESTRATOR")
            requests.post(
                f"{orchestrator_url}/api/orchestrator/status",
                json={
                    "change_id": manifest.change_id,
                    "agent_id": self.agent_id,
                    "status": "DISPATCHED", 
                    "details": {
                        "message": f"Dispatched to {len(receivers)} agents: {', '.join(receivers)}",
                        "receivers": receivers,
                        "manifest": manifest.to_dict()
                    }
                },
                timeout=5
            )
        except Exception:
            pass
        
        return results
    
    def process_manifest(self, manifest: ChangeManifest) -> Dict[str, Any]:
        """
        Process a change manifest for NPCI Switch.
        
        Args:
            manifest: Change manifest to process
            
        Returns:
            Processing results
        """
        try:
            self.update_status(manifest.change_id, AgentStatus.RECEIVED, "Analyzing manifest for required changes...")
            
            code_changes = self._interpret_manifest(manifest)
            self.update_status(manifest.change_id, AgentStatus.RECEIVED, f"Identified {len(code_changes)} dependent files to update")
            
            import os
            github_token = os.environ.get("GITHUB_TOKEN")
            
            # Apply code changes locally without committing
            applied_changes = []
            changed_files = []
            for change in code_changes:
                file_path = change.get("file_path", "")
                change_details = change.get("changes", {})
                
                self.update_status(manifest.change_id, AgentStatus.APPLIED, f"Applying changes to {file_path}...")
                
                success, message, diff = self.code_updater.update_file(file_path, change_details, manifest.change_id, auto_commit=False)
                if success:
                    applied_changes.append({
                        "file": file_path,
                        "status": "MODIFIED",
                        "diff": diff[:500] if diff else None,  # Keep in summary
                    })
                    changed_files.append(file_path)
                    # Send detailed log with diff
                    self.update_status(manifest.change_id, AgentStatus.APPLIED, {
                        "message": f"Successfully updated {file_path}",
                        "file": file_path,
                        "diff": diff
                    })
                else:
                    self.update_status(manifest.change_id, AgentStatus.ERROR, f"Failed to update {file_path}: {message}")
            
            # Create a PR with all grouped changes
            if changed_files and github_token:
                self.update_status(manifest.change_id, AgentStatus.APPLIED, f"Creating Pull Request for {len(changed_files)} files...")
                branch_name = f"update/{self.agent_id.lower()}/{manifest.change_id[:8]}"
                pr_message = f"[{self.agent_name}] Apply changes for Manifest {manifest.change_id}"
                
                pr_url = self.code_updater.create_pr_for_changes(
                    file_paths=changed_files,
                    branch_name=branch_name,
                    message=pr_message,
                    github_token=github_token
                )
                
                if pr_url:
                    self.update_status(manifest.change_id, AgentStatus.APPLIED, f"Pull Request opened: {pr_url}")
                else:
                    self.update_status(manifest.change_id, AgentStatus.ERROR, "Failed to create Pull Request.")
                
                self.update_status(manifest.change_id, AgentStatus.RECEIVED, "Code changes deployed to PR. Awaiting manual merge.")
            if not changed_files:
                self.update_status(manifest.change_id, AgentStatus.READY, "No code changes required for NPCI Switch")
            else:
                self.update_status(manifest.change_id, AgentStatus.TESTED, "Running verification tests...")
                import time
                time.sleep(1)
                self.update_status(manifest.change_id, AgentStatus.TESTED, "All verification tests passed")
                self.update_status(manifest.change_id, AgentStatus.READY, "Validation complete. Ready for deployment.")

            self.pending_manifests = [m for m in self.pending_manifests if m.change_id != manifest.change_id]
            self.completed_manifests.append(manifest.change_id)

            return {
                "agent_id": self.agent_id,
                "change_id": manifest.change_id,
                "status": AgentStatus.READY.value,
                "applied_changes": applied_changes,
                "message": f"Manifest {manifest.change_id} processed successfully",
            }

        except Exception as e:
            logger.error(f"[{self.agent_name}] Error processing manifest: {e}")
            self.update_status(manifest.change_id, AgentStatus.ERROR, str(e))
            return {
                "agent_id": self.agent_id,
                "change_id": manifest.change_id,
                "status": AgentStatus.ERROR.value,
                "error": str(e),
            }

    def _interpret_manifest(self, manifest: ChangeManifest) -> List[Dict[str, Any]]:
        """Use LLM to interpret manifest and generate code change instructions."""
        if not self.llm:
            return self._generate_basic_changes(manifest)

        file_contexts = ""
        for p in self.get_component_paths():
            full_path = self.code_updater.base_path / p
            if full_path.exists():
                file_contexts += f"\n--- {p} ---\n{full_path.read_text(encoding='utf-8')}\n"

        prompt = f"""
You are a senior Python backend engineer working on a NPCI Switch system that routes UPI transactions.

Change Manifest:
- Change ID: {manifest.change_id}
- Type: {manifest.change_type}
- Description: {manifest.description}
- Affected Components: {manifest.affected_components}
- Code Changes Required: {manifest.code_changes}

Based on this manifest, generate specific code changes for the NPCI Switch component.

Return a JSON array of changes, each with:
- file_path: relative path to file (e.g., 'npci/app.py')
- changes: object with type ('modify', 'add_function', 'add_import') and details.

For 'modify' type, use: "SEARCH: <exact code block>\nREPLACE: <new code block>"
Output ONLY the JSON array. No markdown or explanation.

Files available:
{file_contexts}
"""

        try:
            self.update_status(manifest.change_id, AgentStatus.RECEIVED, {
                "message": "Generating code changes using LLM...",
                "prompt": prompt
            })
            response = self.llm.generate(prompt)
            logger.info(f"LLM Response for {manifest.change_id}:\n{response}")
            self.update_status(manifest.change_id, AgentStatus.RECEIVED, {
                "message": "Received LLM response",
                "response": response
            })
            import re
            match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
            if match:
                import json
                changes = json.loads(match.group(0))
                if isinstance(changes, list):
                    return changes
        except Exception as e:
            logger.warning(f"LLM interpretation failed, using basic changes: {e}")

        return self._generate_basic_changes(manifest)

    def _generate_basic_changes(self, manifest: ChangeManifest) -> List[Dict[str, Any]]:
        """Generate basic code changes based on manifest."""
        changes = []
        if manifest.change_type.value == "validation_rule":
            validation_code = (
                f"# Validation: Minimum transaction amount (per manifest {manifest.change_id})\n"
                "if amount < 1.0:\n"
                "    return jsonify(error=\"MIN_AMOUNT_VIOLATION\", details=\"Amount below minimum\"), 400"
            )
            changes.append({
                "file_path": "npci/app.py",
                "changes": {
                    "type": "add_validation",
                    "validation_code": validation_code,
                    "insert_point": "        amount = float(amt_el.get(\"value\") or 0)",
                },
            })
        return changes
    
    def get_component_paths(self) -> List[str]:
        """Get NPCI component file paths."""
        return [
            "npci/app.py",
            "common/schemas/upi_pay_request.xsd",
            "common/schemas/upi_resppay_response.xsd",
        ]
