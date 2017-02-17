###########################################################
###########################################################
####                                                   ####
####          CALCULATE MEAN SQUARE ERROR              ####                 
####                                                   ####
####    Adaptation to python of the Fiji plugin SNR    ####
####    written by Daniel Sage Biomedical Image Group, ####
####    EPFL, Switzerland, webpage:                    ####
####         http://bigwww.epfl.ch/sage/soft/snr/      ####
####                                                   #### 
####    Author: Filippo Arcadu, arcusfil@gmail.com,    ####
####                      26/06/2014                   ####
####                                                   ####
###########################################################
########################################################### 




####  PYTHON MODULES
from __future__ import print_function,division
import time
import argparse
import sys
import os
import glob
import datetime
import numpy as np
import math




####  MY MODULES
sys.path.append( '../common/' )
import my_image_io as io 
import my_image_display as dis
import my_image_process as proc




####  MY VARIABLES
myfloat = np.float64




###########################################################
###########################################################
####                                                   ####
####                 GET INPUT ARGUMENTS               ####                 
####                                                   ####
###########################################################
########################################################### 

def getArgs():
    parser = argparse.ArgumentParser(description='''Calculates SNR , PSNR , RMSE
                                                  and MAE between two images.''',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-i1','--image1',dest='image1',
                        help = 'Select reference image')
    
    parser.add_argument('-i2','--image2',dest='image2',
                        help = 'Select an image / images to analyze; if'
                        + ' more images are selected use a ":" to separate them')
    
    parser.add_argument('-D','--path',dest='path',
                        help = 'Select a path to a bunch of images to analyze')
    
    parser.add_argument('-s','--scaling',dest='scaling',action='store_true',
                        help = 'Enable scaling procedure to fit the interval'
                        +'of grey values to the image/s to analyze with that of'
                        +' the reference image')
    
    parser.add_argument('-t','--register',dest='register',action='store_true',
                        help = 'Enable registration of the image to be analized'
                        +' with the oracle')  

    parser.add_argument('-c','--resol_circle',dest='resol_circle',action='store_true',
                        help = 'Enable analisys only inside the resolution circle')  

    parser.add_argument('-r','--roi',dest='roi',
                        help = 'Select region of interest; e.g. -r x0:y0,x1:y1'
                        + ' or -r path/roi.txt ( file generated by "Get Roi Pixels" )'
                        + ' plugin for Fiji')

    parser.add_argument('-g','--grad',dest='gradient', action='store_true',
                        help = 'Run the analysis on the gradient images of the inputs')    

    parser.add_argument('-p','--plot',dest='plot',action='store_true',
                        help='Enable plots to check whether the orientation'
                        +' of the images is correct')

    parser.add_argument('-i3',dest='logpath',
                        help='Specify path for logfile')  

    parser.add_argument('-l',dest='log',action='store_true',
                        help='Enable extensed logfile')    
                        
    args = parser.parse_args()
    
    if args.image1 is None:
        parser.print_help()
        sys.exit('\nERROR: Reference image not specified!\n')
    
    if args.image2 is None and args.path is None:
        parser.print_help()
        sys.exit('\nERROR: Neither single image nor bunch of images'
                 + ' to analyze specified!\n')     
    
    return args




###########################################################
###########################################################
####                                                   ####
####        DECOMPOSE INTEGER NUMBER IN FACTORS        ####                 
####                                                   ####
###########################################################
###########################################################

def factors( n ):
    result = []
    for i in range(2,n+1): 
        s = 0;
        while n/i == math.floor(n/float(i)): 
            n = n/float(i)
            s += 1
        if s > 0:
            for k in range(s):
                result.append(i) 
            if n == 1:
                return result




###########################################################
###########################################################
####                                                   ####
####               COMPUTE GRADIENT IMAGE              ####                 
####                                                   ####
###########################################################
###########################################################

def compute_gradient_image( image ):
    grad_image = np.gradient( image )
    grad_image = np.array( grad_image ).reshape( 2 , image.shape[0] , image.shape[1] )
    sqr_grad_image = np.sqrt( grad_image[0,:,:]**2 + grad_image[1,:,:]**2 )
    return sqr_grad_image




###########################################################
###########################################################
####                                                   ####
####                FIGURES OF MERIT                   ####                 
####                                                   ####
###########################################################
###########################################################

##  Notation:
##  r(x,y)  --->  reference image
##  t(x,y)  --->  test image
##  nx , ny --->  number of rown and columns


##  SNR ---> SIGNAL TO NOISE RATIO
##
##  SNR = 10 * log_{10}( ( sum_{x}sum_{y} [ r(x,y) ]^2 ) /
##                sum_{x}sum_{y} [ r(x,y) - t(x,y) ]^2 )    

def calc_snr( oracle , image ):
    num = np.sum( oracle * oracle )
    den = np.sum( ( oracle - image ) * ( oracle - image ) )
    SNR = 10 * np.log10( num / den )
    return SNR



##  PSNR ---> PEAK SIGNAL TO NOISE RATIO EXPRESSED IN dB
##
##  PSNR = 10 * log_{10}( ( max( r(x,y) ]^2 ) /
##  ( 1/( nx * ny ) * sum_{x}sum_{y} [ r(x,y) - t(x,y) ]^2 )   

def calc_psnr( oracle , image ):
    nx , ny = image.shape
    factor = 1.0 / ( nx * ny )
    num = ( np.max( oracle ) )**2
    den = factor * np.sum( ( oracle - image ) * ( oracle - image ) )
    PSNR = 10 * np.log10( num / den )
    return PSNR



##  RMSE ---> ROOT MEAN SQUARE ERROR
##
##  RMSE = 1/( nx * ny ) * sum_{x}sum_{y} [ r(x,y) - t(x,y) ]^2 

def calc_rmse( oracle , image ):
    nx , ny = image.shape 
    RMSE = np.sqrt( 1.0/myfloat( nx * ny ) * \
           np.sum( ( oracle - image ) * ( oracle - image ) ) )
    return RMSE



##  MAE ---> MEAN ABSOLUTE ERROR
##
##  MAE = 1/( nx * ny ) * sum_{x}sum_{y} | r(x,y) - t(x,y) |      

def calc_mae( oracle , image ):
    nx , ny = image.shape 
    MAE = 1.0/myfloat( nx * ny ) * \
          np.sum( np.abs( oracle - image ) ) 
    return MAE




###########################################################
###########################################################
####                                                   ####
####                  WRITE LOG FILE                   ####                 
####                                                   ####
###########################################################
########################################################### 

def write_log_file( args , image_list , results ): 
    ##  Open the file
    if args.logpath is None:
        fileout = args.image2[:len(args.image2)-4] + '_psnr_analysis.txt'
    else:
        logpath = args.logpath
        if logpath[len(logpath)-1] != '/':
            logpath += '/'
        chunks = args.image2[:len(args.image2)-4].split( '/' )
        name   = chunks[len(chunks)-1]
        fileout = logpath + name + '_snr.txt'          
    fp = open( fileout , 'w' )  


    if args.log is True:
        ##  Initial logo
        fp.write('\n')
        fp.write('\n#######################################')
        fp.write('\n#######################################') 
        fp.write('\n###                                 ###')
        fp.write('\n###        MEAN SQUARE ERROR        ###')
        fp.write('\n###                                 ###')
        fp.write('\n#######################################')
        fp.write('\n#######################################') 
        fp.write('\n')


        ##  Date
        today = datetime.datetime.now()
        fp.write('\nMean square error calculation performed on the '
                      + str(today))   


        ##  Print oracle image file
        fp.write('\n\nReading reference image:\n' + args.image1)


        ##  Linear regression
        if args.scaling is True:
            fp.write('\n\nLinear regression option enabled')


        ##  Image registration
        if args.register is True:
            fp.write('\n\nImage registration option enabled')


        ##  Select resolution circle
        if args.resol_circle is True:
            fp.write('\n\nSelecting the resolution circle')


        ##  Crop image
        if args.roi is not None:
            if args.roi.find(',') != -1:
                roi = args.roi

                if args.roi.find(',') != -1:
                    roi = roi.split(',')
                    p0 = [int(roi[0].split(':')[1]),int(roi[0].split(':')[0])]
                    p1 = [int(roi[1].split(':')[1]),int(roi[1].split(':')[0])]

                fp.write('\n\nCropping rectangular ROI with vertices:  ( ' \
                         + str(p0[0]) + ' , ' + str(p0[1]) + ')   (' + \
                        str(p1[0]) + ' , ' + str(p1[1]) + ')')
        
            else:
                fp.write('\n\nUsing pixels specified in file:\n' + args.roi )  

    
    ##  Summary of the results
    num_img = len( image_list )
    for i in range( num_img ):
        if args.log is True:
            fp.write('\n\nTest image number ' + str( i ) + '\n' + image_list[i] )
        fp.write('\nSNR = ' + str( results[i][0] ))
        fp.write('\nPSNR = ' + str( results[i][1] ))   
        fp.write('\nRMSE = ' + str( results[i][2] ))   
        fp.write('\nMAE = ' + str( results[i][3] ))

    fp.write('\n')


    ##  Close the file
    fp.close()




###########################################################
###########################################################
####                                                   ####
####                         MAIN                      ####                 
####                                                   ####
###########################################################
###########################################################   

def main():
    print('\n')
    print('#######################################')
    print('#######################################') 
    print('###                                 ###')
    print('###         MEAN SQUARE ERROR       ###')
    print('###                                 ###')
    print('#######################################')
    print('#######################################') 
    print('\n')

    
    
    ##  Get input arguments
    args = getArgs()


    
    ##  Get oracle image 
    currDir = os.getcwd()
    image1 = io.readImage( args.image1 )
    image1 = image1.astype(myfloat)
    
    print('\nReading reference image:\n', args.image1)
    print('Image shape: ', image1.shape)


    image_list = []
    results = []

    
    
    ##  CASE OF SINGLE IMAGE TO ANALYZE
    if args.image2 is not None:
        if args.image2.find( ':' ) == -1:
            image_list.append( args.image2 )
            image2 = io.readImage( args.image2 ) 
            image2 = image2.astype(myfloat)
            num_img = 1
            
            print('\nReading image to analyze:\n', args.image2)
            print('Image shape: ', image2.shape)


            ##  Get time in which the prgram starts to run
            time1 = time.time()      


            ##  Scale image to analyze with respect to the reference one
            if args.scaling is True:
                print('\nPerforming linear regression ....')
                image2 =  proc.linear_regression( image1 , image2 )


            ##  Register images
            if args.register is True:
                print('\nPerforming registration of the image to analize ....')
                image2 = proc.image_registration( image2 , image1 , 'ssd' )


            ##  Crop resolution circle of the images
            if args.resol_circle is True:
                print('\nSelecting the resolution circle')
                image1 = proc.select_resol_square( image1 )
                image2 = proc.select_resol_square( image2 )                


            ##  Crop images if enabled
            if args.roi is not None:
                roi = args.roi

                if args.roi.find(',') != -1:
                    roi = roi.split(',')
                    p0 = [int(roi[0].split(':')[1]),int(roi[0].split(':')[0])]
                    p1 = [int(roi[1].split(':')[1]),int(roi[1].split(':')[0])]
                
                    print('Cropping rectangular ROI with vertices:  ( ', \
                            p0[0],' , ', p0[1], ')   ( ', p1[0],' , ',p1[1], ')')
                
                    image1 = proc.crop_image( image1 , p0 , p1 )
                    image2 = proc.crop_image( image2 , p0 , p1 )

                else:
                    print('\nUsing pixels specified in file:\n', roi)
                    file_roi = open( roi , 'r' )
                    pixels = np.loadtxt( file_roi )
                    image1 = image1[pixels[:,0],pixels[:,1]]
                    image2 = image2[pixels[:,0],pixels[:,1]]
                    num_pix = len( image1 )
                    fact = factors( num_pix )
                    image1 = image1.reshape( fact[0] , int( num_pix/fact[0] ) )
                    image2 = image2.reshape( fact[0] , int( num_pix/fact[0] ) )   


            ##  Compute the gradient of the images, if enabled
            if args.gradient is True:
                image1 = compute_gradient_image( image1 )
                image2 = compute_gradient_image( image2 )      


            ##  Check whether the 2 images have the same shape
            if image1.shape != image2.shape:
                sys.error('\nERROR: The input images have different shapes!\n')


            ##  Plot to check whether the images have the same orientation
            if args.plot is True:
                print('\nPlotting images to check orientation ....')
                img_list = [ image1 , image2 ]
                title_list = [ 'Oracle image' , 'Image to analyze' ]
                dis.plot_multi( img_list , title_list , 'Check plot' )    


            ##  Compute figures of merit
            SNR = calc_snr( image1 , image2 )
            PSNR = calc_psnr( image1 , image2 )
            RMSE = calc_rmse( image1 , image2 )
            MAE = calc_rmse( image1 , image2 ) 

            results.append( np.array( [ SNR , PSNR , RMSE , MAE ] ) )



        ##  CASE OF MULTIPLE SPECIFIC IMAGES
        else:
            image_list = args.image2.split(':')
            img_list = [ ]
            title_list = [ ]
            num_img = len( image_list ) 

            for im in range( num_img ):
                img_file = image_list[im]
                image1 = io.readImage( args.image1 )
                image2 = io.readImage( img_file )  # image2 --> image to analyze
                image2 = image2.astype(myfloat)
                print('\nReading image to analyze:\n', args.image2)
                print('Image shape: ', image2.shape)


                ##  Get time in which the prgram starts to run
                time1 = time.time()      


                ## Scale image to analyze with respect to the reference one
                if args.scaling is True:
                    print('\nPerforming linear regression ....')
                    image2 =  proc.linearRegression( image1 , image2 )


                ## Register images
                if args.register is True:
                    print('\nPerforming registration of the image to analize ....') 
                    image2 = proc.image_registration( image2 , image1 , 'ssd' ) 


                ##  Crop resolution circle of the images
                if args.resol_circle is True:
                    print('\nSelecting the resolution circle')
                    image1 = proc.selectResolutionSquare( image1 )
                    image2 = proc.selectResolutionSquare( image2 )


                ##  Crop images if enabled
                if args.roi is not None:
                    roi = args.roi

                    if args.roi.find(',') != -1:
                        roi = roi.split(',')
                        p0 = [int(roi[0].split(':')[1]),int(roi[0].split(':')[0])]
                        p1 = [int(roi[1].split(':')[1]),int(roi[1].split(':')[0])]
                
                        print('Cropping rectangular ROI with vertices:  ( ', \
                                p0[0],' , ', p0[1], ')   ( ', p1[0],' , ',p1[1], ')')
                
                        image1 = proc.crop_image( image1 , p0 , p1 )
                        image2 = proc.crop_image( image2 , p0 , p1 )

                    else:
                        print('\nUsing pixels specified in file:\n', roi) 
                        file_roi = open( roi , 'r' )
                        pixels = np.loadtxt( file_roi )
                        pixels = pixels.astype( int )

                        image1 = image1[pixels[:,0],pixels[:,1]]
                        image2 = image2[pixels[:,0],pixels[:,1]]
                        num_pix = len( image1 )
                        fact = factors( num_pix )
                        image1 = image1.reshape( fact[0] , int( num_pix/fact[0] ) )
                        image2 = image2.reshape( fact[0] , int( num_pix/fact[0] ) )       


                ##  Compute the gradient of the images, if enabled
                if args.gradient is True:
                    image1 = compute_gradient_image( image1 )
                    image2 = compute_gradient_image( image2 )      
                
                
                ##  Check whether the 2 images have the same shape
                if image1.shape != image2.shape:
                    sys.exit('\nERROR: The input images have different shapes!\n')


                ##  Plot to check whether the images have the same orientation
                if args.plot is True:
                    print('\nPlotting images to check orientation ....')
                    img_list2 = [ image1 , image2 ]
                    title_list2 = [ 'Oracle image' , 'Image to analyze' ]
                    dis.plot_multi( img_list2 , title_list2 , 'Check plot' )


                ##  Compute figures of merit
                SNR = calc_snr( image1 , image2 )
                PSNR = calc_psnr( image1 , image2 )
                RMSE = calc_rmse( image1 , image2 )
                MAE = calc_rmse( image1 , image2 )

                results.append( np.array( [ SNR , PSNR , RMSE , MAE ] ) )                                  



    ##  CASE OF BUNCH OF IMAGES TO ANALYZE 
    else:
        os.chdir(args.path)
        image_list = sorted(glob.glob('*'))
        num_img = len(fileIn)

        ## Get time in which the prgram starts to run
        time1 = time.time()


        ## Loop on all the images to analyze
        for i in range( num_img ):
            image1 = io.readImage( args.image1 )
            image2 = io.readImage( image_list[i] )
            image2 = image2.astype(myfloat)
            print('\n\n\nIMAGE TO ANALYZE NUMBER: ', i)
            print('\nReading image to analyze:\n', image_list[i])
            print('Image shape: ', image2.shape)

            if args.fileout is not None:
                fileout.write('\nReading image to analyze:\n' + fileIn[i])    


            ## Scale image to analyze with respect to the reference one
            if args.scaling is True:
                print('\nPerforming linear regression ....')
                image2 =  proc.linearRegression( image1 , image2 )


            ## Register images
            if args.register is True:
                print('\nPerforming registration of the image to analize ....') 
                image2 = proc.image_registration( image2 , image1 , 'ssd' )  


            ##  Crop resolution circle of the images
            if args.resol_circle is True:
                print('\nSelecting the resolution circle')
                image1 = proc.selectResolutionSquare( image1 )
                image2 = proc.selectResolutionSquare( image2 )


            ##  Crop images if enabled
            if args.roi is not None:
                roi = args.roi

                if args.roi.find(',') != -1:
                    roi = roi.split(',')
                    p0 = [int(roi[0].split(':')[1]),int(roi[0].split(':')[0])]
                    p1 = [int(roi[1].split(':')[1]),int(roi[1].split(':')[0])]
                
                    print('Cropping rectangular ROI with vertices:  ( ', \
                            p0[0],' , ', p0[1], ')   ( ', p1[0],' , ',p1[1], ')')
                
                    image1 = proc.crop_image( image1 , p0 , p1 )
                    image2 = proc.crop_image( image2 , p0 , p1 )

                else:
                    print('\nUsing pixels specified in file:\n', roi) 
                    file_roi = open( roi , 'r' )
                    pixels = np.loadtxt( file_roi )
                    pixels = pixels.astype( int )

                    image1 = image1[pixels[:,0],pixels[:,1]]
                    image2 = image2[pixels[:,0],pixels[:,1]]
                    num_pix = len( image1 )
                    fact = factors( num_pix )
                    image1 = image1.reshape( fact[0] , int( num_pix/fact[0] ) )
                    image2 = image2.reshape( fact[0] , int( num_pix/fact[0] ) ) 


                ##  Check whether the 2 images have the same shape
                if image1.shape != image2.shape:
                    sys.exit('\nERROR: The input images have different shapes!\n')


            ##  Compute the gradient of the images, if enabled
            if args.gradient is True:
                image1 = compute_gradient_image( image1 )
                image2 = compute_gradient_image( image2 )


            ##  Plot to check whether the images have the same orientation
            if args.plot is True and args.roi.find(',') != -1:
                print('\nPlotting images to check orientation ....')
                img_list2 = [ image1 , image2 ]
                title_list2 = [ 'Oracle image' , 'Image to analyze' ]
                dis.plot_multi( img_list2 , title_list2 , 'Check plot' )       


            ##  Compute figures of merit
            SNR = calc_snr( image1 , image2 )
            PSNR = calc_psnr( image1 , image2 )
            RMSE = calc_rmse( image1 , image2 )
            MAE = calc_rmse( image1 , image2 )

            results.append( np.array( [ SNR , PSNR , RMSE , MAE ] ) )  


        os.chdir(currDir)



    ##  Summary print of the results
    print('\n\nSUMMARY OF THE RESULTS:\n')
    print('\nReference image:\n', args.image1)

    for i in range( num_img ):
        print('\n\nTest image number ', i,'\n', image_list[i],'\n')
        print('SNR = ' , results[i][0])
        print('PSNR = ' , results[i][1])   
        print('MRSE = ' , results[i][2])   
        print('MAE = ' , results[i][3])   



    ##  Get time elapsed for the run of the program
    time2 = time.time() - time1
    print('\n\nTime elapsed for the calculation: ', time2)



    ##  Write log file
    write_log_file( args , image_list , results )

    print('\n\n') 




###########################################################
###########################################################
####                                                   ####
####                    CALL TO MAIN                   ####                 
####                                                   ####
###########################################################
###########################################################  

if __name__ == '__main__':
    main()