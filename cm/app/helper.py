import uuid
import ast
import json

import os


from zipfile import ZipFile

import zipfile
def generate_output_file_tif(output_directory):
    return generate_output_file_with_extension(output_directory,'.tif')

def generate_output_file_zip(output_directory):
    return generate_output_file_with_extension(output_directory,'.zip')
def generate_output_file_csv(output_directory):
    return generate_output_file_with_extension(output_directory, '.csv')

def generate_output_file_shp(output_directory):
    return generate_output_file_with_extension(output_directory, '.shp')


def generate_output_file_with_extension(output_directory,extension):
    filename = str(uuid.uuid4()) + extension
    output_raster_path = output_directory+'/'+filename  # output raster
    return output_raster_path

def validateJSON(value):
    #print (message + 'type', type(value))
    response = ast.literal_eval(json.dumps(value))

    return response


def create_zip_shapefiles(output_directory, shafefile):
    print ("shafefile",shafefile)
    os.chdir(output_directory)
    # determine file name
    filename = shafefile.replace(output_directory+'/', "")
    filename = filename.encode("utf-8") # Get what we need
    import time
    zinfo = zipfile.ZipInfo(filename, time.localtime(os.getmtime(filename))[0:6])
    print ("shafefile",shafefile)
    zip_file = filename.replace('.shp', '.zip')
    shp_file = filename
    print ("shp_file",shp_file)
    dbf_file = filename.replace('.shp', '.dbf')
    print ("dbf_file",dbf_file)
    prj_file = filename.replace('.shp', '.prj')
    print ("prj_file",prj_file)
    shx_file = filename.replace('.shp', '.shx')
    print ("shx_file",shx_file)
    zf = ZipFile(zip_file, 'w')
    print ("zf",zf)

    #try:
    zf.write(dbf_file)
    zf.write(prj_file)
    zf.write(shx_file)
    zf.write(shp_file)


    #finally:
    print ("zfclose")
    zf.close()
    print ("zip_file ",zip_file)
    return zip_file

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

def zip_directory(path_to_zip):
    print ('path_to_zip ',path_to_zip)
    filename = str(uuid.uuid4()) + '.zip'

    zipf = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)
    zipdir(path_to_zip, zipf)
    zipf.close()
    return path_to_zip

def generate_directory(tile_path):
    access_rights = 0o755
    print ('***********WILL gENERATE DIRECTORY AT {} *******************************',tile_path)

    try:
        os.mkdir(tile_path, access_rights)
    except OSError:
        print ("Creation of the directory %s failed" % tile_path)
    else:
        print ("Successfully created the directory %s" % tile_path)







