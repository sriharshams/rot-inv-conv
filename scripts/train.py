from __future__ import print_function

try:
    import time

    import os
    import sys
    import yaml
    import time
    import argparse
    import numpy as np

    import matplotlib as mpl
    import matplotlib.pyplot as plt

    from riconv.model import conv_model
    from riconv.dir_utils import DataDirStruct, ModelDirStruct
    from riconv.load_data import train_img_generator, test_img_generator

except ImportError as e:
    print(e)
    raise ImportError

def main():
    global args
    parser = argparse.ArgumentParser(description="Convolutional NN Training Script")
    parser.add_argument("-c", "--config", dest="configfile", default='config.yml', help="Path to yaml configuration file")
    parser.add_argument("-m", "--modelnames", dest="modelnames", nargs="*", default=None, required=False, help="Model name to test")
    args = parser.parse_args()

    # Get configuration file
    with open(args.configfile, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # Extract config parameters
    trainpath = cfg.get('dataset', '')

    # List of available models
    avail_models = cfg.get('models_to_run', '').split(',')
    # Get requested models, if None, take config list
    model_list = args.modelnames
    if model_list is None:
        model_list = avail_models

    # Print basic info
    print("\n\n... Starting ...")
    print("\nConfiguration file: {}".format(args.configfile))
    print("\nData set location: {}\n".format(trainpath))
    print("About to train {} model(s)\n".format(len(model_list)))

    # Loop over requested models
    for mod_i in model_list:
        mod_i = mod_i.strip()

        # Get config file parameters
        outpath = cfg.get(mod_i).get('outpath', os.path.join(trainpath, 'saved_models', mod_i))
        val_split = cfg.get(mod_i).get('validation_split', 0.2)
        batch_size = cfg.get(mod_i).get('batch_size', 128)
        epochs = cfg.get(mod_i).get('epochs', -1)
        rotation_range = cfg.get(mod_i).get('rotation_range', 0.)
        layer_string_list = cfg.get(mod_i).get('layers', 'conv2d, conv2d, conv2d, conv2d')
        layer_string_list = [lay.strip() for lay in layer_string_list.split(',')]

        print("Model {} details:\n\t{}\n".format(mod_i, cfg.get(mod_i)))

        # Directory structures for data and model saving
        data_dir_struct = DataDirStruct(trainpath)
        model_dir_struct = ModelDirStruct(outpath)

        # Training and validation generators
        train_gen, valid_gen = train_img_generator(dir_struct=data_dir_struct,
                                                   batch_size=batch_size,
                                                   rotation_range=rotation_range,
                                                   val_split=val_split)
       
        # Time training
        start_t = time.time()

        # Train the model
        history, trained_model = conv_model(dir_struct=model_dir_struct,
                                            train_gen=train_gen,
                                            valid_gen=valid_gen,
                                            epochs=epochs,
                                            layer_string_list=layer_string_list)

        # Get training time estimate
        elapsed = time.time() - start_t
        print("Estimated time to train: {}".format(elapsed))

        # Test the model on a subset
        print("Running model on the test set...\n")

        # Testing generator
        test_gen = test_img_generator(dir_struct=data_dir_struct,
                                      batch_size=1,
                                      fixed_rotation=False,
                                      rotation_angle=rotation_range)
        
        # Show scores for a subset
        scores = trained_model.evaluate_generator(test_gen, steps=None, verbose=1)
        print("Testing %s: %.2f%%\n" % (trained_model.metrics_names[1], scores[1]*100))

    print("\nDone training and testing.\n")

if __name__ == "__main__":
    main()