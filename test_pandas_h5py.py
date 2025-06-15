import h5py
import pandas as pd
import numpy as np
import os
import sys

def test_pandas_h5py_compatibility():
    """
    Test that pandas and h5py work together correctly.
    """
    print("Testing pandas and h5py compatibility...")
    print(f"pandas version: {pd.__version__}")
    print(f"h5py version: {h5py.__version__}")
    print(f"numpy version: {np.__version__}")
    print(f"Python version: {sys.version}")
    
    # Create a temporary file
    filename = "test_pandas_h5py.h5"
    
    try:
        # Create a pandas DataFrame
        df = pd.DataFrame({
            'A': np.random.rand(10),
            'B': np.random.rand(10),
            'C': np.random.rand(10)
        })
        
        print("\nCreated pandas DataFrame:")
        print(df.head())
        
        # Save DataFrame to HDF5 file using pandas
        df.to_hdf(filename, key='df', mode='w')
        print(f"\nSaved DataFrame to {filename}")
        
        # Read DataFrame from HDF5 file using pandas
        df_read = pd.read_hdf(filename, key='df')
        print("\nRead DataFrame from HDF5 file using pandas:")
        print(df_read.head())
        
        # Verify data integrity
        if df.equals(df_read):
            print("\n✅ Data integrity check passed: Original and read DataFrames are identical")
        else:
            print("\n❌ Data integrity check failed: Original and read DataFrames are different")
        
        # Access the HDF5 file directly using h5py
        with h5py.File(filename, 'r') as f:
            print("\nHDF5 file structure:")
            print(list(f.keys()))
            
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return False
        
    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
            print(f"\nRemoved temporary file: {filename}")

if __name__ == "__main__":
    test_pandas_h5py_compatibility()