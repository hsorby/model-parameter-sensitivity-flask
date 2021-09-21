import os
import unittest

from mps_server.libcellml_tools import get_parameters_from_model


class PreparationTestCase(unittest.TestCase):

    def test_model(self):
        base_directory = os.environ['MPS_BASE_DIR']
        model_location = os.path.join(base_directory, 'ohara_rudy_cipa_v2_2017.cellml')
        result = get_parameters_from_model(model_location)

        print(result)
        self.assertTrue(isinstance(result, dict))


if __name__ == '__main__':
    unittest.main()
