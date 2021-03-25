#Functions for reading in single cell imaging data
#Joshua Hess

#Import necessary modules
import skimage.io
import h5py
import pandas as pd
import numpy as np
import os
import skimage.measure as measure

from pathlib import Path
import csv


def gini_index(mask, intensity):
    x = intensity[mask]
    sorted_x = np.sort(x)
    n = len(x)
    cumx = np.cumsum(sorted_x, dtype=float)
    return (n + 1 - 2 * np.sum(cumx) / cumx[-1]) / n


def MaskChannel(mask_loaded, image_loaded_z, intensity_props = ["mean_intensity"]):
    """Function for quantifying a single channel image

    Returns a table with CellID according to the mask and the mean pixel intensity
    for the given channel for each cell"""
    builtin_props = set(intensity_props).intersection(measure._regionprops.PROP_VALS)
    extra_props = set(intensity_props).difference(measure._regionprops.PROP_VALS)
    dat = measure.regionprops_table(
        mask_loaded, image_loaded_z,
        properties = tuple(builtin_props),
        extra_properties = [globals()[n] for n in extra_props]
    )
    return dat


def MaskIDs(mask):
    """This function will extract the CellIDs and the XY positions for each
    cell based on that cells centroid

    Returns a dictionary object"""

    dat = measure.regionprops_table(
        mask,
        properties=("label", "centroid", "area", "major_axis_length", "minor_axis_length", "eccentricity", "solidity", "extent", "orientation")
    )

    IDs = {
        "CellID": "label",
        "X_centroid": "centroid-1",
        "Y_centroid": "centroid-0",
        "column_centroid": "centroid-1",
        "row_centroid": "centroid-0",
        "Area": "area",
        "MajorAxisLength": "major_axis_length",
        "MinorAxisLength": "minor_axis_length",
        "Eccentricity": "eccentricity",
        "Solidity": "solidity",
        "Extent": "extent",
        "Orientation": "orientation",
    }

    dat_formatted = {
        k: dat[v] for k, v in IDs.items()
    }

    return dat_formatted


def PrepareData(image,z):
    """Function for preparing input for maskzstack function. Connecting function
    to use with mc micro ilastik pipeline"""

    image_path = Path(image)

    #Check to see if image tif(f)
    if image_path.suffix == '.tiff' or image_path.suffix == '.tif' or image_path.suffix == '.btf':
        #Check to see if the image is ome.tif(f)
        if  image.endswith(('.ome.tif','.ome.tiff')):
            #Read the image
            image_loaded_z = skimage.io.imread(image,img_num=z,plugin='tifffile')
            #print('OME TIF(F) found')
        else:
            #Read the image
            image_loaded_z = skimage.io.imread(image,img_num=z,plugin='tifffile')
            #print('TIF(F) found')
            # Remove extra axis
            #image_loaded = image_loaded.reshape((image_loaded.shape[1],image_loaded.shape[3],image_loaded.shape[4]))

    #Check to see if image is hdf5
    elif image_path.suffix == '.h5' or image_path.suffix == '.hdf5':
        #Read the image
        f = h5py.File(image,'r+')
        #Get the dataset name from the h5 file
        dat_name = list(f.keys())[0]
        ###If the hdf5 is exported from ilastik fiji plugin, the dat_name will be 'data'
        #Get the image data
        image_loaded = np.array(f[dat_name])
        #Remove the first axis (ilastik convention)
        image_loaded = image_loaded.reshape((image_loaded.shape[1],image_loaded.shape[2],image_loaded.shape[3]))
        ###If the hdf5 is exported from ilastik fiji plugin, the order will need to be
        ###switched as above --> z_stack = np.swapaxes(z_stack,0,2) --> z_stack = np.swapaxes(z_stack,0,1)

    #Return the objects
    return image_loaded_z


def MaskZstack(masks_loaded,image,channel_names_loaded, intensity_props = ["mean_intensity"]):
    """This function will extract the stats for each cell mask through each channel
    in the input image

    mask_loaded: dictionary containing Tiff masks that represents the cells in your image.

    z_stack: Multichannel z stack image"""

    #Get the names of the keys for the masks dictionary
    mask_names = list(masks_loaded.keys())
    #Get the CellIDs for this dataset by using only a single mask (first mask)
    IDs = pd.DataFrame(MaskIDs(masks_loaded[mask_names[0]]))
    #Create empty dictionary to store channel results per mask
    dict_of_chan = {m_name: [] for m_name in mask_names}
    #Get the z channel and the associated channel name from list of channel names
    for z in range(len(channel_names_loaded)):
        #Run the data Prep function
        image_loaded_z = PrepareData(image,z)

        #Iterate through number of masks to extract single cell data
        for nm in range(len(mask_names)):
            #Use the above information to mask z stack
            dict_of_chan[mask_names[nm]].append(
                MaskChannel(masks_loaded[mask_names[nm]],image_loaded_z, intensity_props = intensity_props)
            )
        #Print progress
        print("Finished "+str(z))

    #Iterate through the rest of the masks to modify names of channels and convert to data table
    for nm in mask_names:
        #Create channel names for this mask
        new_names = [channel_names_loaded[i]+"_"+str(nm) for i in range(len(channel_names_loaded))]
        #Convert the channel names list and the list of intensity values to a dictionary and combine with CellIDs and XY
        dict_of_chan[nm] = pd.concat(
            [
                pd.DataFrame(dict(zip(new_names, [x["mean_intensity"] for x in dict_of_chan[nm]])))
            ] + [
                pd.DataFrame(dict(zip([n + "_" + prop_n for n in new_names], [x[prop_n] for x in dict_of_chan[nm]]))) for prop_n
                in set(intensity_props).difference(["mean_intensity"])
            ],
            axis=1
        )

    #Concatenate all data from all masks to return
    dat = pd.concat([IDs] + [dict_of_chan[nm] for nm in mask_names], axis=1)

    #Get the name of the columns in the dataframe so we can reorder to histoCAT convention
    cols = list(dat.columns.values)
    #Reorder the list (Move xy position to end with spatial information)
    cols.append(cols.pop(cols.index("X_centroid")))
    cols.append(cols.pop(cols.index("Y_centroid")))
    cols.append(cols.pop(cols.index("column_centroid")))
    cols.append(cols.pop(cols.index("row_centroid")))
    cols.append(cols.pop(cols.index("Area")))
    cols.append(cols.pop(cols.index("MajorAxisLength")))
    cols.append(cols.pop(cols.index("MinorAxisLength")))
    cols.append(cols.pop(cols.index("Eccentricity")))
    cols.append(cols.pop(cols.index("Solidity")))
    cols.append(cols.pop(cols.index("Extent")))
    cols.append(cols.pop(cols.index("Orientation")))
    #Reindex the dataframe with new order
    dat = dat.reindex(columns=cols)

    #Return the dataframe
    return dat


def ExtractSingleCells(masks,image,channel_names,output, intensity_props = ["mean_intensity"]):
    """Function for extracting single cell information from input
    path containing single-cell masks, z_stack path, and channel_names path."""

    #Create pathlib object for output
    output = Path(output)

    #Check if header available
    #sniffer = csv.Sniffer()
    #sniffer.has_header(open(channel_names).readline())
    #If header not available
    #if not sniffer:
        #If header available
        #channel_names_loaded = pd.read_csv(channel_names)
        #channel_names_loaded_list = list(channel_names_loaded.marker_name)
    #else:
        #print("negative")
        #old one column version
        #channel_names_loaded = pd.read_csv(channel_names,header=None)
        #Add a column index for ease
        #channel_names_loaded.columns = ["marker"]
        #channel_names_loaded = list(channel_names_loaded.marker.values)

    #Read csv channel names
    channel_names_loaded = pd.read_csv(channel_names)
    #Check for size of columns
    if channel_names_loaded.shape[1] > 1:
        #Get the marker_name column if more than one column (CyCIF structure)
        channel_names_loaded_list = list(channel_names_loaded.marker_name)
    else:
        #old one column version -- re-read the csv file and add column name
        channel_names_loaded = pd.read_csv(channel_names, header = None)
        #Add a column index for ease and for standardization
        channel_names_loaded.columns = ["marker"]
        channel_names_loaded_list = list(channel_names_loaded.marker)

    #Check for unique marker names -- create new list to store new names
    channel_names_loaded_checked = []
    for idx,val in enumerate(channel_names_loaded_list):
        #Check for unique value
        if channel_names_loaded_list.count(val) > 1:
            #If unique count greater than one, add suffix
            channel_names_loaded_checked.append(val + "_"+ str(channel_names_loaded_list[:idx].count(val) + 1))
        else:
            #Otherwise, leave channel name
            channel_names_loaded_checked.append(val)

    #Clear small memory amount by clearing old channel names
    channel_names_loaded, channel_names_loaded_list = None, None

    #Read the masks
    masks_loaded = {}
    #iterate through mask paths and read images to add to dictionary object
    for m in masks:
        m_full_name = os.path.basename(m)
        m_name = m_full_name.split('.')[0]
        masks_loaded.update({str(m_name):skimage.io.imread(m,plugin='tifffile')})

    scdata_z = MaskZstack(masks_loaded,image,channel_names_loaded_checked, intensity_props = intensity_props)
    #Write the singe cell data to a csv file using the image name

    im_full_name = os.path.basename(image)
    im_name = im_full_name.split('.')[0]
    scdata_z.to_csv(str(Path(os.path.join(str(output),str(im_name+".csv")))),index=False)


def MultiExtractSingleCells(masks,image,channel_names,output, intensity_props = ["mean_intensity"]):
    """Function for iterating over a list of z_stacks and output locations to
    export single-cell data from image masks"""

    print("Extracting single-cell data for "+str(image)+'...')

    #Run the ExtractSingleCells function for this image
    ExtractSingleCells(masks,image,channel_names,output, intensity_props = intensity_props)

    #Print update
    im_full_name = os.path.basename(image)
    im_name = im_full_name.split('.')[0]
    print("Finished "+str(im_name))
