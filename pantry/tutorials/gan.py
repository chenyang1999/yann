"""
Referenced from 

Goodfellow, Ian, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, 
Aaron Courville, and Yoshua Bengio. "Generative adversarial nets." In Advances in Neural Information
 Processing Systems, pp. 2672-2680. 2014.

 Todo:

    Deconvolutional GAN is throwing a wierd error. 
"""
from yann.special.gan import gan 
from theano import tensor as T 

def shallow_gan_mnist ( dataset= None, verbose = 1 ):
    """
    This function is a demo example of a generative adversarial network. 
    This is an example code. You should study this code rather than merely run it.  

    Args: 
        dataset: Supply a dataset.    
        verbose: Similar to the rest of the dataset.

    Notes:
        This method is setup for MNIST.
    """
    optimizer_params =  {        
                "momentum_type"       : 'polyak',             
                "momentum_params"     : (0.65, 0.9, 50),      
                "regularization"      : (0.000, 0.000),       
                "optimizer_type"      : 'rmsprop',                
                "id"                  : "main"
                        }


    dataset_params  = {
                            "dataset"   : dataset,
                            "type"      : 'xy',
                            "id"        : 'data'
                    }

    visualizer_params = {
                    "root"       : 'shallow_gan/',
                    "frequency"  : 1,
                    "sample_size": 225,
                    "rgb_filters": False,
                    "debug_functions" : False,
                    "debug_layers": True,  
                    "id"         : 'main'
                        }  
                      
    # intitialize the network
    net = gan (      borrow = True,
                     verbose = verbose )                       
    
    net.add_module ( type = 'datastream', 
                     params = dataset_params,
                     verbose = verbose )    
    
    net.add_module ( type = 'visualizer',
                     params = visualizer_params,
                     verbose = verbose 
                    ) 

    
    net.add_module ( type = 'optimizer',
                     params = optimizer_params,
                     verbose = verbose 
                    ) 

    #z - latent space created by random layer
    net.add_layer(type = 'random',
                        id = 'z',
                        num_neurons = (100,32), 
                        distribution = 'normal',
                        mu = 0,
                        sigma = 1,
                        verbose = verbose)
    
    #x - inputs come from dataset 1 X 784
    net.add_layer ( type = "input",
                    id = "x",
                    verbose = verbose, 
                    datastream_origin = 'data', # if you didnt add a dataset module, now is 
                                                 # the time. 
                    mean_subtract = False )

    net.add_layer ( type = "dot_product",
                    origin = "z",
                    id = "G(z)",
                    num_neurons = 784,
                    activation = 'tanh',
                    verbose = verbose
                    )  # This layer is the one that creates the images.
        
    #D(x) - Contains params theta_d creates features 1 X 800. 
    net.add_layer ( type = "dot_product",
                    id = "D(x)",
                    origin = "x",
                    num_neurons = 800,
                    activation = 'relu',
                    regularize = True,                                                         
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D(G(z))",
                    origin = "G(z)",
                    input_params = net.dropout_layers["D(x)"].params, 
                    num_neurons = 800,
                    activation = 'relu',
                    regularize = True,
                    verbose = verbose
                    )


    #C(D(x)) - This is the opposite of C(D(G(z))), real
    net.add_layer ( type = "dot_product",
                    id = "real",
                    origin = "D(x)",
                    num_neurons = 1,
                    activation = 'sigmoid',
                    verbose = verbose
                    )

    #C(D(G(z))) fake - the classifier for fake/real that always predicts fake 
    net.add_layer ( type = "dot_product",
                    id = "fake",
                    origin = "D(G(z))",
                    num_neurons = 1,
                    activation = 'sigmoid',
                    input_params = net.dropout_layers["real"].params, # Again share their parameters                    
                    verbose = verbose
                    )

    
    #C(D(x)) - This is the opposite of C(D(G(z))), real
    net.add_layer ( type = "classifier",
                    id = "softmax",
                    origin = "D(x)",
                    num_classes = 10,
                    activation = 'softmax',
                    verbose = verbose
                   )
    
    # objective layers 
    # discriminator objective 
    net.add_layer (type = "tensor",
                    input =  - 0.5 * T.mean(T.log(net.layers['real'].output)) - \
                                  0.5 * T.mean(T.log(1-net.layers['fake'].output)),
                    input_shape = (1,),
                    id = "discriminator_task"
                    )

    net.add_layer ( type = "objective",
                    id = "discriminator_obj",
                    origin = "discriminator_task",
                    layer_type = 'value',
                    objective = net.dropout_layers['discriminator_task'].output,
                    datastream_origin = 'data', 
                    verbose = verbose
                    )
    #generator objective 
    net.add_layer (type = "tensor",
                    input =  - 0.5 * T.mean(T.log(net.layers['fake'].output)),
                    input_shape = (1,),
                    id = "objective_task"
                    )
    net.add_layer ( type = "objective",
                    id = "generator_obj",
                    layer_type = 'value',
                    origin = "objective_task",
                    objective = net.dropout_layers['objective_task'].output,
                    datastream_origin = 'data', 
                    verbose = verbose
                    )   

    #softmax objective.    
    net.add_layer ( type = "objective",
                    id = "classifier_obj",
                    origin = "softmax",
                    objective = "nll",
                    layer_type = 'discriminator',
                    datastream_origin = 'data', 
                    verbose = verbose
                    )
    
    from yann.utils.graph import draw_network
    draw_network(net.graph, filename = 'gan.png')    
    net.pretty_print()
    
    net.cook (  objective_layers = ["classifier_obj", "discriminator_obj", "generator_obj"],
                optimizer_params = optimizer_params,
                discriminator_layers = ["D(x)"],
                generator_layers = ["G(z)"], 
                classifier_layers = ["D(x)", "softmax"],                                                
                softmax_layer = "softmax",
                game_layers = ("fake", "real"),
                verbose = verbose )
                    
    learning_rates = (0.05, 0.01 )  

    net.train( epochs = (20), 
               k = 2,  
               pre_train_discriminator = 3,
               validate_after_epochs = 1,
               visualize_after_epochs = 1,
               training_accuracy = True,
               show_progress = True,
               early_terminate = True,
               verbose = verbose)
                           
    return net

def deep_gan_mnist (dataset, verbose = 1 ):
    """
    This function is a demo example of a generative adversarial network. 
    This is an example code. You should study this code rather than merely run it.  

    Args: 
        dataset: Supply a dataset.    
        verbose: Similar to the rest of the dataset.

    Returns:
        net: A Network object.

    Notes:
        This network here mimics
        Ian Goodfellow's original code and implementation for MNIST adapted from his source code:
        https://github.com/goodfeli/adversarial/blob/master/mnist.yaml .It might not be a perfect 
        replicaiton, but I tried as best as I could.

        This method is setup for MNIST
    """
    if verbose >=2:
        print (".. Creating a GAN network")

    optimizer_params =  {        
                "momentum_type"       : 'polyak',             
                "momentum_params"     : (0.5, 0.7, 20),      
                "regularization"      : (0.000, 0.000),       
                "optimizer_type"      : 'adagrad',                
                "id"                  : "main"
                        }


    dataset_params  = {
                            "dataset"   : dataset,
                            "type"      : 'xy',
                            "id"        : 'data'
                    }

    visualizer_params = {
                    "root"       : 'deep_gan/',
                    "frequency"  : 1,
                    "sample_size": 225,
                    "rgb_filters": False,
                    "debug_functions" : False,
                    "debug_layers": True,  
                    "id"         : 'main'
                        }  
                    
    # intitialize the network
    net = gan (      borrow = True,
                    verbose = verbose )                       
    
    net.add_module ( type = 'datastream', 
                    params = dataset_params,
                    verbose = verbose )    
    
    net.add_module ( type = 'visualizer',
                    params = visualizer_params,
                    verbose = verbose 
                    ) 

    #z - latent space created by random layer
    net.add_layer(type = 'random',
                        id = 'z',
                        num_neurons = (100,32), 
                        distribution = 'normal',
                        mu = 0,
                        sigma = 1,
                        # limits = (0,1),
                        verbose = verbose)
    
    #x - inputs come from dataset 1 X 784
    net.add_layer ( type = "input",
                    id = "x",
                    verbose = verbose, 
                    datastream_origin = 'data', # if you didnt add a dataset module, now is 
                                                # the time. 
                    mean_subtract = False )

    # Generator layers
    net.add_layer ( type = "dot_product",
                    origin = "z",
                    id = "G1",
                    num_neurons = 1200,
                    activation = 'relu',
                    # batch_norm = True,
                    verbose = verbose
                    ) 

    net.add_layer ( type = "dot_product",
                    origin = "G1",
                    id = "G2",
                    num_neurons = 1200,
                    activation = 'relu',
                    # batch_norm = True,
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    origin = "G2",
                    id = "G(z)",
                    num_neurons = 784,
                    activation = 'tanh',
                    verbose = verbose
                    )  # This layer is the one that creates the images.
        
    #D(x) - Contains params theta_d creates features 1 X 800. 
    # Discriminator Layers
    net.add_layer ( type = "unflatten",
                    origin = "G(z)",
                    id = "G(z)-unflattened",
                    shape = (28,28),
                    verbose = verbose )


    net.add_layer ( type = "dot_product",
                    id = "D1-x",
                    origin = "x",
                    num_neurons = 1200,
                    activation = ('maxout','maxout',5),
                    regularize = True,  
                    # batch_norm = True,
                    # dropout_rate = 0.5,                                                       
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D1-z",
                    origin = "G(z)-unflattened",
                    input_params = net.dropout_layers["D1-x"].params, 
                    num_neurons = 1200,
                    activation = ('maxout','maxout',5),
                    regularize = True,
                    # batch_norm = True,
                    # dropout_rate = 0.5,                       
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D2-x",
                    origin = "D1-x",
                    num_neurons = 1200,
                    activation = ('maxout','maxout',5),
                    regularize = True,       
                    # batch_norm = True,
                    # dropout_rate = 0.5,                                                                         
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D2-z",
                    origin = "D1-z",
                    input_params = net.dropout_layers["D2-x"].params, 
                    num_neurons = 1200,
                    activation = ('maxout','maxout',5),
                    regularize = True,
                    # dropout_rate = 0.5,          
                    # batch_norm = True,                    
                    verbose = verbose
                    )

    #C(D(x)) - This is the opposite of C(D(G(z))), real
    net.add_layer ( type = "dot_product",
                    id = "D(x)",
                    origin = "D2-x",
                    num_neurons = 1,
                    activation = 'sigmoid',
                    verbose = verbose
                    )

    #C(D(G(z))) fake - the classifier for fake/real that always predicts fake 
    net.add_layer ( type = "dot_product",
                    id = "D(G(z))",
                    origin = "D2-z",
                    num_neurons = 1,
                    activation = 'sigmoid',
                    input_params = net.dropout_layers["D(x)"].params,                   
                    verbose = verbose
                    )

    
    #C(D(x)) - This is the opposite of C(D(G(z))), real
    net.add_layer ( type = "classifier",
                    id = "softmax",
                    origin = "D2-x",
                    num_classes = 10,
                    activation = 'softmax',
                    verbose = verbose
                )
    
    # objective layers 
    # discriminator objective 
    net.add_layer (type = "tensor",
                    input =  - 0.5 * T.mean(T.log(net.layers['D(x)'].output)) - \
                                0.5 * T.mean(T.log(1-net.layers['D(G(z))'].output)),
                    input_shape = (1,),
                    id = "discriminator_task"
                    )

    net.add_layer ( type = "objective",
                    id = "discriminator_obj",
                    origin = "discriminator_task",
                    layer_type = 'value',
                    objective = net.dropout_layers['discriminator_task'].output,
                    datastream_origin = 'data', 
                    verbose = verbose
                    )
    #generator objective 
    net.add_layer (type = "tensor",
                    input =  - 0.5 * T.mean(T.log(net.layers['D(G(z))'].output)),
                    input_shape = (1,),
                    id = "objective_task"
                    )
    net.add_layer ( type = "objective",
                    id = "generator_obj",
                    layer_type = 'value',
                    origin = "objective_task",
                    objective = net.dropout_layers['objective_task'].output,
                    datastream_origin = 'data', 
                    verbose = verbose
                    )   
    
    #softmax objective.    
    net.add_layer ( type = "objective",
                    id = "classifier_obj",
                    origin = "softmax",
                    objective = "nll",
                    layer_type = 'discriminator',
                    datastream_origin = 'data', 
                    verbose = verbose
                    )
    
    # from yann.utils.graph import draw_network
    # draw_network(net.graph, filename = 'gan.png')    
    net.pretty_print()
    
    net.cook (  objective_layers = ["classifier_obj", "discriminator_obj", "generator_obj"],
                optimizer_params = optimizer_params,
                discriminator_layers = ["D1-x","D2-x"],
                generator_layers = ["G1","G2","G(z)"], 
                classifier_layers = ["D1-x","D2-x","softmax"],                                                
                softmax_layer = "softmax",
                game_layers = ("D(x)", "D(G(z))"),
                verbose = verbose )
                    
    learning_rates = (0.00004, 0.001 )  

    net.train( epochs = (20), 
            k = 1, 
            pre_train_discriminator = 3,
            validate_after_epochs = 1,
            visualize_after_epochs = 1,
            training_accuracy = True,
            show_progress = True,
            early_terminate = True,
            verbose = verbose)

def deep_deconvolutional_gan(dataset,
                              regularize = True,
                              batch_norm = True,
                              dropout_rate = 0.5,
                              verbose = 1 ):
    """
    This function is a demo example of a generative adversarial network. 
    This is an example code. You should study this code rather than merely run it.  
    This method uses a few deconvolutional layers.
    This method is setup to produce images of size 32X32.

    Args:         
        dataset: Supply a dataset.    
        regularize: ``True`` (default) supplied to layer arguments
        batch_norm: ``True`` (default) supplied to layer arguments
        dropout_rate: ``None`` (default) supplied to layer arguments
        verbose: Similar to the rest of the dataset.

    Returns:
        net: A Network object.

    Notes:
        This method is setup for Cifar 10.
    """
    if verbose >=2:
        print (".. Creating a GAN network")

    optimizer_params =  {        
                "momentum_type"       : 'false',             
                "momentum_params"     : (0.51, 0.95, 40),      
                "regularization"      : (0.00001, 0.00001),       
                "optimizer_type"      : 'adam',                
                "id"                  : "main"
                        }


    dataset_params  = {
                            "dataset"   : dataset,
                            "type"      : 'xy',
                            "id"        : 'data'
                    }

    visualizer_params = {
                    "root"       : 'dcgan/',
                    "frequency"  : 1,
                    "sample_size": 225,
                    "rgb_filters": True,
                    "debug_functions" : False,
                    "debug_layers": False,  
                    "id"         : 'main'
                        }  
                    
    # intitialize the network
    net = gan (      borrow = True,
                    verbose = verbose )                       
    
    net.add_module ( type = 'datastream', 
                    params = dataset_params,
                    verbose = verbose )    
    
    net.add_module ( type = 'visualizer',
                    params = visualizer_params,
                    verbose = verbose 
                    ) 

    #z - latent space created by random layer
    net.add_layer(type = 'random',
                        id = 'z',
                        num_neurons = (500,128), 
                        distribution = 'normal',
                        mu = 0,
                        sigma = 1,
                        limits = (0,1),
                        verbose = verbose)

    # Generator layers
    net.add_layer ( type = "dot_product",
                    origin = "z",
                    id = "G1",
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,
                    verbose = verbose
                    ) 

    net.add_layer ( type = "dot_product",
                    origin = "G1",
                    id = "G2",
                    num_neurons = 5408,
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,
                    verbose = verbose
                    )

    net.add_layer ( type = "unflatten",
                    origin = "G2",
                    id = "G2-unflatten",
                    shape = (13, 13, 32),
                    batch_norm = batch_norm,
                    verbose = verbose
                    )

    net.add_layer ( type = "deconv",
                    origin = "G2-unflatten",
                    id = "G3",
                    num_neurons = 32,
                    filter_size = (3,3),
                    output_shape = (28,28,32),
                    activation = 'relu',
                    regularize = regularize,    
                    batch_norm = batch_norm,
                    stride = (2,2),
                    verbose = verbose
                    )

    net.add_layer ( type = "deconv",
                    origin = "G3",
                    id = "G(z)",
                    num_neurons = 32,
                    filter_size = (5,5),
                    output_shape = (32,32,3),
                    activation = 'tanh',
                    # regularize = regularize,    
                    stride = (1,1),
                    verbose = verbose
                    )
    
    #x - inputs come from dataset 1 X 784
    net.add_layer ( type = "input",
                    id = "x",
                    verbose = verbose, 
                    datastream_origin = 'data', # if you didnt add a dataset module, now is 
                                                # the time. 
                    mean_subtract = False )

    #D(x) - Contains params theta_d creates features 1 X 800. 
    # Discriminator Layers
    # add first convolutional layer

    net.add_layer ( type = "conv_pool",
                    origin = "x",
                    id = "D1-x",
                    num_neurons = 20,
                    filter_size = (5,5),
                    pool_size = (2,2),
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,                    
                    verbose = verbose
                    )

    net.add_layer ( type = "conv_pool",
                    origin = "G(z)",
                    id = "D1-z",
                    num_neurons = 20,
                    filter_size = (5,5),
                    pool_size = (2,2),
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,
                    input_params = net.dropout_layers["D1-x"].params,
                    verbose = verbose
                    )
    
    net.add_layer ( type = "conv_pool",
                    origin = "D1-x",
                    # origin = "x",
                    id = "D2-x",
                    num_neurons = 50,
                    filter_size = (3,3),
                    pool_size = (2,2),
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,                    
                    verbose = verbose
                    )      

    net.add_layer ( type = "conv_pool",
                    origin = "D1-z",
                    # origin = "G(z)",
                    id = "D2-z",
                    num_neurons = 50,
                    filter_size = (3,3),
                    pool_size = (2,2),
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,                    
                    input_params = net.dropout_layers["D2-x"].params,
                    verbose = verbose
                    )      

    net.add_layer ( type = "dot_product",
                    id = "D3-x",
                    origin = "D2-x",
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,  
                    batch_norm = batch_norm,
                    dropout_rate = dropout_rate,                                                       
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D3-z",
                    origin = "D2-z",
                    input_params = net.dropout_layers["D3-x"].params, 
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,
                    dropout_rate = dropout_rate,                       
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D4-x",
                    origin = "D3-x",
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,       
                    batch_norm = batch_norm,
                    dropout_rate = dropout_rate,                                                                         
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D4-z",
                    origin = "D3-z",
                    input_params = net.dropout_layers["D4-x"].params, 
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,
                    dropout_rate = dropout_rate,          
                    batch_norm = batch_norm,                    
                    verbose = verbose
                    )

    #C(D(x)) - This is the opposite of C(D(G(z))), real
    net.add_layer ( type = "dot_product",
                    id = "D(x)",
                    origin = "D4-x",
                    num_neurons = 1,
                    activation = 'sigmoid',
                    regularize = regularize,
                    verbose = verbose
                    )

    #C(D(G(z))) fake - the classifier for fake/real that always predicts fake 
    net.add_layer ( type = "dot_product",
                    id = "D(G(z))",
                    origin = "D4-z",
                    num_neurons = 1,
                    activation = 'sigmoid',
                    regularize = regularize,
                    input_params = net.dropout_layers["D(x)"].params,                   
                    verbose = verbose
                    )

    
    #C(D(x)) - This is the opposite of C(D(G(z))), real
    net.add_layer ( type = "classifier",
                    id = "softmax",
                    origin = "D4-x",
                    num_classes = 10,
                    regularize = regularize,
                    activation = 'softmax',
                    verbose = verbose
                )
    
    # objective layers 
    # discriminator objective 
    net.add_layer (type = "tensor",
                    input =  - 0.5 * T.mean(T.log(net.layers['D(x)'].output)) - \
                                0.5 * T.mean(T.log(1-net.layers['D(G(z))'].output)),
                    input_shape = (1,),
                    id = "discriminator_task"
                    )

    net.add_layer ( type = "objective",
                    id = "discriminator_obj",
                    origin = "discriminator_task",
                    layer_type = 'value',
                    objective = net.dropout_layers['discriminator_task'].output,
                    datastream_origin = 'data', 
                    verbose = verbose
                    )
    #generator objective 
    net.add_layer (type = "tensor",
                    input =  - 0.5 * T.mean(T.log(net.layers['D(G(z))'].output)),
                    input_shape = (1,),
                    id = "objective_task"
                    )
    net.add_layer ( type = "objective",
                    id = "generator_obj",
                    layer_type = 'value',
                    origin = "objective_task",
                    objective = net.dropout_layers['objective_task'].output,
                    datastream_origin = 'data', 
                    verbose = verbose
                    )   
    
    #softmax objective.    
    net.add_layer ( type = "objective",
                    id = "classifier_obj",
                    origin = "softmax",
                    objective = "nll",
                    layer_type = 'discriminator',
                    datastream_origin = 'data', 
                    verbose = verbose
                    )
    
    # from yann.utils.graph import draw_network
    # draw_network(net.graph, filename = 'gan.png')    
    net.pretty_print()
    
    net.cook (  objective_layers = ["classifier_obj", "discriminator_obj", "generator_obj"],
                optimizer_params = optimizer_params,
                discriminator_layers = ["D1-x", "D2-x","D3-x","D4-x"],
                generator_layers = ["G1","G2","G3","G(z)"], 
                classifier_layers = ["D1-x", "D2-x","D3-x","D4-x","softmax"],                                                
                softmax_layer = "softmax",
                game_layers = ("D(x)", "D(G(z))"),
                verbose = verbose )
                    
    learning_rates = (0.0004, 0.0001 )  

    net.train( epochs = (20), 
            k = 1, 
            pre_train_discriminator = 2,
            validate_after_epochs = 1,
            visualize_after_epochs = 1,
            training_accuracy = True,
            show_progress = True,
            early_terminate = True,
            verbose = verbose)

    return net

def deep_deconvolutional_lsgan(dataset,
                              regularize = True,
                              batch_norm = True,
                              dropout_rate = 0.5,
                              verbose = 1 ):
    """
    This function is a demo example of a generative adversarial network. 
    This is an example code. You should study this code rather than merely run it.  
    This method uses a few deconvolutional layers as was used in the DCGAN paper.
    This method is setup to produce images of size 32X32. 

    Args:         
        dataset: Supply a dataset.    
        regularize: ``True`` (default) supplied to layer arguments
        batch_norm: ``True`` (default) supplied to layer arguments
        dropout_rate: ``None`` (default) supplied to layer arguments
        verbose: Similar to the rest of the dataset.

    Returns:
        net: A Network object.

    Notes:
        This method is setupfor SVHN / CIFAR10.
        This is an implementation of th least squares GAN with a = 0, b = 1 and c= 1 (equation 9)
        [1] Least Squares Generative Adversarial Networks, Xudong Mao, Qing Li, Haoran Xie, Raymond Y.K. Lau, Zhen Wang
    """
    if verbose >=2:
        print (".. Creating a GAN network")

    optimizer_params =  {        
                "momentum_type"       : 'false',             
                "momentum_params"     : (0.55, 0.9, 20),      
                "regularization"      : (0.00001, 0.00001),       
                "optimizer_type"      : 'adam',                
                "id"                  : "main"
                        }


    dataset_params  = {
                            "dataset"   : dataset,
                            "type"      : 'xy',
                            "id"        : 'data'
                    }

    visualizer_params = {
                    "root"       : 'lsgan/',
                    "frequency"  : 1,
                    "sample_size": 225,
                    "rgb_filters": True,
                    "debug_functions" : False,
                    "debug_layers": False,  
                    "id"         : 'main'
                        }  
                    
    # intitialize the network
    net = gan (      borrow = True,
                    verbose = verbose )                       
    
    net.add_module ( type = 'datastream', 
                    params = dataset_params,
                    verbose = verbose )    
    
    net.add_module ( type = 'visualizer',
                    params = visualizer_params,
                    verbose = verbose 
                    ) 

    #z - latent space created by random layer
    net.add_layer(type = 'random',
                        id = 'z',
                        num_neurons = (500,32), 
                        distribution = 'normal',
                        mu = 0,
                        sigma = 1,
                        limits = (0,1),
                        verbose = verbose)

    # Generator layers
    net.add_layer ( type = "dot_product",
                    origin = "z",
                    id = "G1",
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,
                    verbose = verbose
                    ) 

    net.add_layer ( type = "dot_product",
                    origin = "G1",
                    id = "G2",
                    num_neurons = 5408,
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,
                    verbose = verbose
                    )

    net.add_layer ( type = "unflatten",
                    origin = "G2",
                    id = "G2-unflatten",
                    shape = (13, 13, 32),
                    batch_norm = batch_norm,
                    verbose = verbose
                    )

    net.add_layer ( type = "deconv",
                    origin = "G2-unflatten",
                    id = "G3",
                    num_neurons = 32,
                    filter_size = (3,3),
                    output_shape = (28,28,64),
                    activation = 'relu',
                    regularize = regularize,    
                    batch_norm = batch_norm,
                    stride = (2,2),
                    verbose = verbose
                    )


    net.add_layer ( type = "deconv",
                    origin = "G3",
                    id = "G4",
                    num_neurons = 64,
                    filter_size = (3,3),
                    output_shape = (30,30,128),
                    activation = 'relu',
                    regularize = regularize,    
                    batch_norm = batch_norm,
                    stride = (1,1),
                    verbose = verbose
                    )

    net.add_layer ( type = "deconv",
                    origin = "G4",
                    id = "G(z)",
                    num_neurons = 128,
                    filter_size = (3,3),
                    output_shape = (32,32,3),
                    activation = 'tanh',
                    regularize = regularize,    
                    stride = (1,1),
                    verbose = verbose
                    )
    
    #x - inputs come from dataset 1 X 784
    net.add_layer ( type = "input",
                    id = "x",
                    verbose = verbose, 
                    datastream_origin = 'data', # if you didnt add a dataset module, now is 
                                                # the time. 
                    mean_subtract = False )

    #D(x) - Contains params theta_d creates features 1 X 800. 
    # Discriminator Layers
    # add first convolutional layer

    net.add_layer ( type = "conv_pool",
                    origin = "x",
                    id = "D1-x",
                    num_neurons = 20,
                    filter_size = (5,5),
                    pool_size = (2,2),
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,                    
                    verbose = verbose
                    )

    net.add_layer ( type = "conv_pool",
                    origin = "G(z)",
                    id = "D1-z",
                    num_neurons = 20,
                    filter_size = (5,5),
                    pool_size = (2,2),
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,
                    input_params = net.dropout_layers["D1-x"].params,
                    verbose = verbose
                    )
    
    net.add_layer ( type = "conv_pool",
                    origin = "D1-x",
                    # origin = "x",
                    id = "D2-x",
                    num_neurons = 50,
                    filter_size = (3,3),
                    pool_size = (2,2),
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,                    
                    verbose = verbose
                    )      

    net.add_layer ( type = "conv_pool",
                    origin = "D1-z",
                    # origin = "G(z)",
                    id = "D2-z",
                    num_neurons = 50,
                    filter_size = (3,3),
                    pool_size = (2,2),
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,                    
                    input_params = net.dropout_layers["D2-x"].params,
                    verbose = verbose
                    )      

    net.add_layer ( type = "dot_product",
                    id = "D3-x",
                    origin = "D2-x",
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,  
                    batch_norm = batch_norm,
                    dropout_rate = dropout_rate,                                                       
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D3-z",
                    origin = "D2-z",
                    input_params = net.dropout_layers["D3-x"].params, 
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,
                    batch_norm = batch_norm,
                    dropout_rate = dropout_rate,                       
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D4-x",
                    origin = "D3-x",
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,       
                    batch_norm = batch_norm,
                    dropout_rate = dropout_rate,                                                                         
                    verbose = verbose
                    )

    net.add_layer ( type = "dot_product",
                    id = "D4-z",
                    origin = "D3-z",
                    input_params = net.dropout_layers["D4-x"].params, 
                    num_neurons = 1200,
                    activation = 'relu',
                    regularize = regularize,
                    dropout_rate = dropout_rate,          
                    batch_norm = batch_norm,                    
                    verbose = verbose
                    )

    #C(D(x)) - This is the opposite of C(D(G(z))), real
    net.add_layer ( type = "dot_product",
                    id = "D(x)",
                    origin = "D4-x",
                    num_neurons = 1,
                    activation = 'sigmoid',
                    regularize = regularize,
                    verbose = verbose
                    )

    #C(D(G(z))) fake - the classifier for fake/real that always predicts fake 
    net.add_layer ( type = "dot_product",
                    id = "D(G(z))",
                    origin = "D4-z",
                    num_neurons = 1,
                    activation = 'sigmoid',
                    regularize = regularize,
                    input_params = net.dropout_layers["D(x)"].params,                   
                    verbose = verbose
                    )

    
    #C(D(x)) - This is the opposite of C(D(G(z))), real
    net.add_layer ( type = "classifier",
                    id = "softmax",
                    origin = "D4-x",
                    num_classes = 10,
                    regularize = regularize,
                    activation = 'softmax',
                    verbose = verbose
                )
    
    # objective layers 
    # discriminator objective 
    net.add_layer (type = "tensor",
                    input =  0.5 * T.mean(T.sqr(net.layers['D(x)'].output-1)) + \
                                0.5 * T.mean(T.sqr(net.layers['D(G(z))'].output)),
                    input_shape = (1,),
                    id = "discriminator_task"
                    )

    net.add_layer ( type = "objective",
                    id = "discriminator_obj",
                    origin = "discriminator_task",
                    layer_type = 'value',
                    objective = net.dropout_layers['discriminator_task'].output,
                    datastream_origin = 'data', 
                    verbose = verbose
                    )
    #generator objective 
    net.add_layer (type = "tensor",
                    input =  0.5 * T.mean(T.sqr(net.layers['D(G(z))'].output-1)),
                    input_shape = (1,),
                    id = "objective_task"
                    )
    net.add_layer ( type = "objective",
                    id = "generator_obj",
                    layer_type = 'value',
                    origin = "objective_task",
                    objective = net.dropout_layers['objective_task'].output,
                    datastream_origin = 'data', 
                    verbose = verbose
                    )   
    
    #softmax objective.    
    net.add_layer ( type = "objective",
                    id = "classifier_obj",
                    origin = "softmax",
                    objective = "nll",
                    layer_type = 'discriminator',
                    datastream_origin = 'data', 
                    verbose = verbose
                    )
    
    # from yann.utils.graph import draw_network
    # draw_network(net.graph, filename = 'gan.png')    
    net.pretty_print()

    net.cook (  objective_layers = ["classifier_obj", "discriminator_obj", "generator_obj"],
                optimizer_params = optimizer_params,
                discriminator_layers = ["D1-x", "D2-x","D3-x","D4-x"],
                generator_layers = ["G1","G2","G3", "G4", "G(z)"], 
                classifier_layers = ["D1-x", "D2-x","D3-x","D4-x","softmax"],                                                
                softmax_layer = "softmax",
                game_layers = ("D(x)", "D(G(z))"),
                verbose = verbose )
                    
    learning_rates = (0.04, 0.0001 )  

    net.train( epochs = (20), 
            k = 1, 
            pre_train_discriminator = 0,
            validate_after_epochs = 1,
            visualize_after_epochs = 1,
            training_accuracy = True,
            show_progress = True,
            early_terminate = True,
            verbose = verbose)

    return net


if __name__ == '__main__':
    
    from yann.special.datasets import cook_mnist_normalized_zero_mean as c 
    # from yann.special.datasets import cook_cifar10_normalized_zero_mean as c
    import sys

    dataset = None  
    if len(sys.argv) > 1:
        if sys.argv[1] == 'create_dataset':
            data = c (verbose = 2)
            dataset = data.dataset_location()
        else:
            dataset = sys.argv[1]
    else:
        print "provide dataset"
    
    if dataset is None:
        print " creating a new dataset to run through"
        data = c (verbose = 2)
        dataset = data.dataset_location() 

    """net = shallow_gan_mnist ( dataset, verbose = 2 )
    net = deep_gan_mnist ( dataset, verbose = 2 )           
    net = deep_deconvolutional_gan ( batch_norm = True,
                                     dropout_rate = 0.5,
                                     regularize = True,
                                     dataset = dataset,
                                     verbose = 2 )"""
    net = deep_deconvolutional_lsgan ( batch_norm = True,
                                     dropout_rate = 0.5,
                                     regularize = True,
                                     dataset = dataset,
                                     verbose = 2 )                                     
