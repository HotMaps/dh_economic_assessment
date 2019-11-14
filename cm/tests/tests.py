import unittest
from werkzeug.exceptions import NotFound
from app import create_app
import os.path
from shutil import copyfile
from .test_client import TestClient
UPLOAD_DIRECTORY = '/var/hotmaps/cm_files_uploaded'

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    os.chmod(UPLOAD_DIRECTORY, 0o777)


class TestAPI(unittest.TestCase):


    def setUp(self):
        self.app = create_app(os.environ.get('FLASK_CONFIG', 'development'))
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.client = TestClient(self.app,)

    def tearDown(self):

        self.ctx.pop()


    def test_compute(self):
        raster_file1_path = 'tests/data/gfa_Wien.tif'
        raster_file2_path = 'tests/data/hdm_Wien.tif'
        #raster_file1_path = 'tests/data/gfa_besancon.tif'
        #raster_file2_path = 'tests/data/hdm_besancon.tif'
        # simulate copy from HTAPI to CM
        save_path1 = UPLOAD_DIRECTORY+"/gfa_Wien.tif"
        save_path2 = UPLOAD_DIRECTORY+"/hdm_Wien.tif"
        copyfile(raster_file1_path, save_path1)
        copyfile(raster_file2_path, save_path2)

        inputs_raster_selection = {}
        inputs_parameter_selection = {}
        inputs_raster_selection["gross_floor_area"]  = save_path1
        inputs_raster_selection["heat"]  = save_path2
        
        inputs_parameter_selection["investment_start_year"] = "2018"
        inputs_parameter_selection["investment_last_year"] = "2030"
        inputs_parameter_selection["depreciation_time"] = "30"
        inputs_parameter_selection["accumulated_energy_saving"] = "0.1"
        inputs_parameter_selection["dh_connection_rate_first_year"] = "0.3"
        inputs_parameter_selection["dh_connection_rate_last_year"] = "0.6"
        inputs_parameter_selection["interest_rate"] = "0.05"
        inputs_parameter_selection["grid_cost_ceiling"] = "25"
        inputs_parameter_selection["c1"] = "212"
        inputs_parameter_selection["c2"] = "4464"
        inputs_parameter_selection["full_load_hours"] = "3000"
        inputs_parameter_selection["mip_gap"] = "0.1"
        
        
        
        # register the calculation module a
        payload = {"inputs_raster_selection": inputs_raster_selection,
                   "inputs_parameter_selection": inputs_parameter_selection}


        rv, json = self.client.post('computation-module/compute/', data=payload)

        self.assertTrue(rv.status_code == 200)


