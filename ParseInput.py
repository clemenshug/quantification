#Functions for parsing command line arguments for ome ilastik prep
import argparse


def ParseInputDataExtract():
   """Function for parsing command line arguments for input to single-cell
   data extraction"""

#if __name__ == '__main__':
   parser = argparse.ArgumentParser()
   parser.add_argument('--masks',nargs='*')
   parser.add_argument('--image')
   parser.add_argument('--channel_names')
   parser.add_argument('--output')
   parser.add_argument(
      '--intensity_props', nargs = "+",
      help="""
         Space separated list of additional metrics to be calculated.
         See list at https://scikit-image.org/docs/dev/api/skimage.measure.html#regionprops
         Additionally available is gini_index, which calculates a single number
         between 0 and 1, representing how unequal the signal is distributed in each region.
         See https://en.wikipedia.org/wiki/Gini_coefficient
      """
   )
   #parser.add_argument('--suffix')
   args = parser.parse_args()
   #Create a dictionary object to pass to the next function
   dict = {'masks': args.masks, 'image': args.image,\
    'channel_names': args.channel_names,'output':args.output,
    'intensity_props': set(args.intensity_props if args.intensity_props is not None else []).union(["mean_intensity"])
   }
   #Print the dictionary object
   print(dict)
   #Return the dictionary
   return dict
