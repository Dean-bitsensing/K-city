import h5py


### h5

def load_h5_data(file_path:str):
    h5_dataset = h5py.File(file_path, 'r')
    return h5_dataset