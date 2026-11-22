"""Offline public-caller contract: no dispatch, token reads or private inputs."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=(ROOT/'.github/workflows/nix-builder.yml').read_text()


class UserspaceForwarding(unittest.TestCase):
    def test_default_is_false_and_forwarding_is_exact(self):
        option=SOURCE.split('      experimental_darwin_userspace:\n',1)[1].split('      timeout_startup:',1)[0]
        self.assertIn('type: boolean',option);self.assertIn('default: false',option)
        self.assertEqual(SOURCE.count('experimental_darwin_userspace: ${{ inputs.experimental_darwin_userspace }}'),1)

    def test_reusable_workflow_is_an_exact_revision(self):
        match=re.search(r'uses: dweee/Nix_Remote-Builders-Distributed/\.github/workflows/nix-builder.yml@([0-9a-f]{40})',SOURCE)
        self.assertIsNotNone(match)
        self.assertEqual(match[1],'bbeb86e5b87bf919c0c905e6ccfde4649ef9b9f9')

    def test_existing_identity_scope_and_niks3_routing_remain(self):
        self.assertIn('tailscale_tags: ${{ inputs.tailscale_tags }}',SOURCE)
        self.assertIn('environment: ${{ inputs.environment != \'\' && inputs.environment || \'\' }}',SOURCE)
        self.assertNotIn('attic',SOURCE.lower())
        self.assertIn('niks3_substitute: "true"',SOURCE)
        self.assertIn('niks3_push: ${{ !inputs.skip_cache_push',SOURCE)
        self.assertNotIn('FORGEJO',SOURCE)


if __name__=='__main__':unittest.main()
