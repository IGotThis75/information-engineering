 
"""
Created on Sun Nov 28 18:27:32 2021

@author: m.benammar
for academic purposes only 
"""
from itertools import product

from matplotlib import pyplot 
import numpy as np 
from PIL import Image as im
import jpeg_functions as fc 
import huffman_functions as hj 

# Quantization matrix 
Q =70; # quality  factor of JPEG in %

Q_matrix = fc.quantization_matrix(Q) # Quantization matrix 
  
# Open the image (obtain an RGB image)
image_origin = im.open("ISAE_Logo_SEIS_Ground_2.PNG")  
image_origin_eval = np.array(image_origin)

# Transform into YCrBR 
image_ycbcr = image_origin.convert('YCbCr') 
image_ycbcr_eval= np.array(image_ycbcr)
 
#  Troncate the image (to make simulations faster)
image_trunc = image_ycbcr_eval[644:724,624:704] 
pyplot.imshow(image_trunc) 
pyplot.savefig("image_trunc_YCbCr.png")  # Saves the plot as a PNG file
print("Plot saved as output_plot.png")


# Initializations
n_row = np.size(image_trunc,0) # Number of rows 
n_col = np.size(image_trunc,1)  # Number of columns
N_blocks =  (np.round(n_row/8 * n_col/8 )).astype(np.int32) # Number of (8x8) blocks 

image_plane_rec = np.zeros((n_row,n_col,3),dtype=np.uint8) 
image_DC = np.zeros((N_blocks.astype(np.int32),3), dtype = np.int32)
image_DC_rec = np.zeros((N_blocks.astype(np.int32),3), dtype = np.int32)
image_AC = np.zeros((63*N_blocks,3),dtype = np.int32 )
image_AC_rec = np.zeros((63*N_blocks,3),dtype = np.int32 )
bits_per_pixel=np.zeros( 3 )
# ---------------------------------------------------------------
#                          Compression 
#  --------------------------------------------------------------

for i_plane in range(0,3): 
    
    # Select a plane  Y, Cb, or Cr 
    image_plane = image_trunc[:,:,i_plane]

    for i_row in range(0,n_row,8): 
        for j_col in range(0,n_col,8):
            
            #  Compute the block number
            block_number =( np.round(i_row/8*(n_row/8)+ j_col/8 )).astype(np.int32)
 
            # Select of block of 8 by 8 pixels
            image_plane_block = image_plane[i_row:i_row+8, j_col:j_col+8]     
            
            # DCT transform
            image_dct = fc.DCT(image_plane_block)
            
            # Quantization
            image_dct_quant = np.round(image_dct/Q_matrix ).astype(np.int32)
            
            # Zigzag reading  
            image_dct_quant_zgzg =  fc.zigzag(image_dct_quant)            
        
            # Separate DC and AC components    
            image_DC[block_number,i_plane] = image_dct_quant_zgzg[0]  
            image_AC[block_number*63 + 1:(block_number+1)*63,i_plane] = image_dct_quant_zgzg[1:63]
    
    # ---- DC components processing    
    # DPCM coding over DC components 
    image_DC_DPCM = image_DC[1:N_blocks,i_plane] - image_DC[0:N_blocks-1,i_plane]
    image_DC_0 = image_DC[0,i_plane] # first DC constant (not compressed)
    
    #  Map the resulting values in categoeries and amplitudes
    image_DC_DPCM_cat = fc.DC_category_vect(image_DC_DPCM) 
    image_DC_DPCM_amp = fc.DC_amplitude_vect(image_DC_DPCM) 
    list_image_cat_DC = np.ndarray.tolist(image_DC_DPCM_cat)  # create a list of DC components
    
    
    # --------------------------Students work on DC components --------------------------------- 
    # Compress with Huffman
    DC_alphabet = np.unique(image_DC_DPCM_cat).tolist()  # Get unique symbols in list form
    frequency_dict_DC, nbr_chr_DC = hj.dict_freq_numbers(list_image_cat_DC, DC_alphabet)  # Generate frequency dictionary
    DC_tree = hj.build_huffman_tree(frequency_dict_DC)  # Build the Huffman tree

    DC_codebook = hj.generate_code(DC_tree)  # Generate codebook (symbol -> Huffman code)
    Compressed_DC_Data = hj.compress(list_image_cat_DC, DC_codebook)  # Compress the data

    # Decompress with Huffman
    DC_decoding_dict = hj.build_decoding_dict(DC_codebook)  # Generate decoding dictionary (Huffman code -> symbol)
    decompressed_cat_DC = hj.decompress(Compressed_DC_Data, DC_decoding_dict)  # Decompress the data

    # Validate decompression
    assert decompressed_cat_DC == list_image_cat_DC, "Decompression failed: data mismatch!"
    print("Compression and decompression successful.")

   
    # ---------------------------------------------------------------------------------------------
    
    # ---- AC components processing 
       
    # RLE coding over AC components  
    AC_coeff = image_AC[:,i_plane] 
    [AC_coeff_rl, AC_coeff_amp]= fc.RLE(AC_coeff)
    list_image_rl_AC = np.ndarray.tolist(AC_coeff_rl)
    
    # --------------------------Students work on AC components ---------------------------------
    # Compress with Huffman
    # Generate the AC alphabet as tuples
    AC_alphabet = list(product(range(16), repeat=2))

    # Convert list_image_rl_AC to tuples
    list_image_rl_AC = [tuple(pair) for pair in list_image_rl_AC]

    # Validate that list_image_rl_AC is not empty and contains valid pairs
    if not list_image_rl_AC:
        raise ValueError("list_image_rl_AC is empty. Cannot compute frequencies.")

    valid_pairs = [pair for pair in list_image_rl_AC if pair in AC_alphabet]
    if not valid_pairs:
        raise ValueError("No valid pairs in list_image_rl_AC match AC_alphabet.")

    # Generate frequency dictionary
    frequency_dict_AC, nbr_chr_AC = hj.dict_freq_numbers_2(list_image_rl_AC, AC_alphabet)
    AC_tree = hj.build_huffman_tree(frequency_dict_AC)  # Build the Huffman tree

    AC_codebook = hj.generate_code_2(AC_tree)  # Generate codebook (symbol -> Huffman code)
    Compressed_AC_Data = hj.compress_2(list_image_rl_AC, AC_codebook)  # Compress the data

    # Decompress with Huffman
    AC_decoding_dict = hj.build_decoding_dict(AC_codebook)  # Generate decoding dictionary (Huffman code -> symbol)
    decompressed_cat_AC = hj.decompress(Compressed_AC_Data, AC_decoding_dict)  # Decompress the data

    # Validate decompression
    assert decompressed_cat_AC == list_image_rl_AC, "Decompression failed: data mismatch!"
    print("Compression and decompression for AC data successful.")

    # Assign decompressed data to a variable
    decompressed_cat_AC = list_image_rl_AC

    # --------------------------------Students work on the nb_bit/ pixel ---------------------
 
     
    
# ---------------------------------------------------------------
#                      Decompression 
#  --------------------------------------------------------------
    # ---- DC components processing  
    # Map the  categories and amplitudes DC components back into values  
    decompressed_cat_DC = np.array(decompressed_cat_DC) 
    image_DC_DPCM_rec = (fc.cat_ampl_to_DC_vect(decompressed_cat_DC,image_DC_DPCM_amp)) 
    
    # DPCM decoding of DC components 
    image_DC_rec[0,i_plane]=image_DC_0
    for i_block in range(1,N_blocks):
        image_DC_rec[i_block,i_plane]= image_DC_rec[i_block-1,i_plane] + image_DC_DPCM_rec[i_block-1]
        
    # ---- AC components processing      
    # Map AC components back into their original values  
    decompressed_cat_AC = np.array(decompressed_cat_AC)  
    image_AC_rec[:,i_plane] =  fc.RLE_inv(decompressed_cat_AC,AC_coeff_amp)

    for i_row in range(0,n_row,8): 
        for j_col in range(0,n_col,8):
            
            block_number = (np.round(i_row/8*(n_row/8)+ j_col/8 )).astype(np.int32)  

            # Combining AC and DC components 
            image_dct_quant_zgzg_rec = np.zeros(64, dtype= np.int32)
            image_dct_quant_zgzg_rec[1:63]= image_AC_rec[block_number*63 + 1:(block_number+1)*63,i_plane]
            image_dct_quant_zgzg_rec[0] = image_DC_rec[block_number,i_plane]
             
            # Inverse zigzag reading  
            image_dct_quant_rec = fc.zigzag_inv(image_dct_quant_zgzg_rec)
            
            # De-Quantization
            image_dct_rec = image_dct_quant_rec*Q_matrix 
            
            # Inverse DCT
            image_rec =  fc.DCT_inv(image_dct_rec) 
            image_plane_rec[i_row:i_row+8, j_col:j_col+8,i_plane ] = image_rec.astype(np.uint8)
            

# Recovering the image from the array of YCbCr
image_ycbcr_rec = im.fromarray(image_plane_rec,'YCbCr')

# Convert back to RGB
image_rec =  image_ycbcr_rec.convert('RGB')

# Plot the image 
pyplot.imshow(image_rec) 
pyplot.savefig("image_rec.png")  # Saves the plot as a PNG file
print("Plot saved as image_rec.png")

 
 
