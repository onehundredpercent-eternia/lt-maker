import unittest
import logging

class ComponentCompilerUnitTests(unittest.TestCase):
    def setUp(self):
        pass
        # Patch out logging below CRITICAL DAMAGE
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)

    def test_check_policies_defined(self):
        from app.engine.component_system import utils

        for policy in utils.ResolvePolicy:
            failure = False
            try:
                eval("utils.{policy}([])".format(policy=policy.value))
            except:
                failure = True
            self.assertFalse(failure, "Did not implement ResolvePolicy %s" % policy.name)
