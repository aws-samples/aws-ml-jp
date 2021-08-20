import argparse
import mxnet as mx
import json
import sys
import os
import gluonnlp as nlp
from mxnet import gluon, autograd
from mxnet.gluon import nn
from bert import data, model
import sys

import logging
logging.basicConfig(level=logging.INFO)


try:
    num_cpus = int(os.environ['SM_NUM_CPUS'])
    num_gpus = int(os.environ['SM_NUM_GPUS'])
except KeyError:
    num_gpus = 0
    
ctx = mx.gpu() if num_gpus > 0 else mx.cpu()
bert_base, vocabulary = nlp.model.get_model('bert_12_768_12', 
                                   dataset_name='wiki_multilingual_uncased', 
                                   pretrained=True, ctx=ctx, use_pooler=True,
                                   use_decoder=False, use_classifier=False)

# The maximum length of an input sequence
max_len = 128

    
if __name__ == '__main__':

    
    # Receive hyperparameters passed via create-training-job API
    parser = argparse.ArgumentParser()

    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--learning-rate', type=float, default=5e-6)
    parser.add_argument('--log-interval', type=float, default=4)

    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--train', type=str, default=os.environ['SM_CHANNEL_TRAIN'])
    parser.add_argument('--current-host', type=str, default=os.environ['SM_CURRENT_HOST'])
    parser.add_argument('--hosts', type=list, default=json.loads(os.environ['SM_HOSTS']))

    args = parser.parse_args()
    
    # Set hyperparameters after parsing the arguments
    batch_size = args.batch_size
    lr = args.learning_rate
    log_interval = args.log_interval
    num_epochs = args.epochs
    current_host = args.current_host
    hosts = args.hosts
    model_dir = args.model_dir
    training_dir = args.train
    
    # Setting for distributed training
    if len(hosts) == 1:
        kvstore = 'device' if num_gpus > 0 else 'local'
    else:
        kvstore = 'dist_device_sync' if num_gpus > 0 else 'dist_sync'
    
    
    
    # Load pre-trained bert model and vocabulary
    # and define the classification model (add classifier and loss function on bert)
    bert_classifier = model.classification.BERTClassifier(bert_base, num_classes=2, dropout=0.1)
    # only need to initialize the classifier layer.
    bert_classifier.classifier.initialize(init=mx.init.Normal(0.02), ctx=ctx)
    bert_classifier.hybridize(static_alloc=True)
    loss_function = mx.gluon.loss.SoftmaxCELoss()
    loss_function.hybridize(static_alloc=True)
    
    # Data loading
    field_separator = nlp.data.Splitter('\t')
    data_train_raw = nlp.data.TSVDataset(filename=os.path.join(training_dir,'train.tsv'), 
                                         field_separator=field_separator)
    
    # Use the vocabulary from pre-trained model for tokenization
    bert_tokenizer = nlp.data.BERTTokenizer(vocabulary, lower=True)

    # The labels for the two classes [(0 : Negative) or  (1 : Poistive)]
    all_labels = ["0", "1"]

    # whether to transform the data as sentence pairs.
    # for single sentence classification, set pair=False
    # for regression task, set class_labels=None
    # for inference without label available, set has_label=False
    pair = False
    transform = data.transform.BERTDatasetTransform(bert_tokenizer, max_len,
                                                    class_labels=all_labels,
                                                    has_label=True,
                                                    pad=True,
                                                    pair=pair)
    data_train = data_train_raw.transform(transform)


    # The FixedBucketSampler and the DataLoader for making the mini-batches
    train_sampler = nlp.data.FixedBucketSampler(lengths=[int(item[1]) for item in data_train],
                                                batch_size=batch_size,
                                                shuffle=True)
    bert_dataloader = mx.gluon.data.DataLoader(data_train, batch_sampler=train_sampler)

    trainer = mx.gluon.Trainer(bert_classifier.collect_params(), 'adam',
                               {'learning_rate': lr, 'epsilon': 1e-9},
                              kvstore=kvstore)

    # Collect all differentiable parameters
    # `grad_req == 'null'` indicates no gradients are calculated (e.g. constant parameters)
    # The gradients for these params are clipped later
    params = [p for p in bert_classifier.collect_params().values() if p.grad_req != 'null']
    grad_clip = 1

    # For evaluation with accuracy
    metric = mx.metric.Accuracy()
    
    # Training loop
    for epoch_id in range(num_epochs):
        metric.reset()
        step_loss = 0
        for batch_id, (token_ids, valid_length, segment_ids, label) in enumerate(bert_dataloader):
            with mx.autograd.record():

                # Load the data to the CPU or GPU
                token_ids = token_ids.as_in_context(ctx)
                valid_length = valid_length.as_in_context(ctx)
                segment_ids = segment_ids.as_in_context(ctx)
                label = label.as_in_context(ctx)

                # Forward computation
                # Loss is weighte by 10 for negaive (0) and 1 for positive(1)
                out = bert_classifier(token_ids, segment_ids, valid_length.astype('float32'))
                ls = loss_function(out, label).mean()

            # And backwards computation
            ls.backward()

            # Gradient clipping
            trainer.allreduce_grads()
            nlp.utils.clip_grad_global_norm(params, 1)
            trainer.update(1)

            step_loss += ls.asscalar()
            metric.update([label], [out])

            # Printing vital information
            if (batch_id + 1) % (log_interval) == 0:
                print('[Epoch {} Batch {}/{}] loss={:.4f}, lr={:.7f}, acc={:.3f}'
                             .format(epoch_id, batch_id + 1, len(bert_dataloader),
                                     step_loss / log_interval,
                                     trainer.learning_rate, metric.get()[1]))
                step_loss = 0
                

    if current_host == hosts[0]:
        bert_classifier.export('%s/model'% model_dir)
        

def model_fn(model_dir):
    """
    Load the gluon model. Called once when hosting service starts.

    :param: model_dir The directory where model files are stored.
    :return: a model (in this case a Gluon network)
    """

    bert_tokenizer = nlp.data.BERTTokenizer(vocabulary, lower=True)
    bert_classifier = gluon.SymbolBlock.imports(
        '%s/model-symbol.json' % model_dir,
        ['data0', 'data1', 'data2'],
        '%s/model-0000.params' % model_dir,
    )
    return {"net": bert_classifier, "tokenizer": bert_tokenizer}


def transform_fn(net, data, input_content_type, output_content_type):
    """
    Transform a request using the Gluon model. Called once per request.

    :param net: The Gluon model.
    :param data: The request payload.
    :param input_content_type: The request content type.
    :param output_content_type: The (desired) response content type.
    :return: response payload and content type.
    """
    # we can use content types to vary input/output handling, but
    # here we just assume json for both
    bert_classifier = net["net"]
    bert_tokenizer = net["tokenizer"]
    
    # Assume one line of text
    parsed = json.loads(data)
    logging.info("Received_data: {}".format(parsed))
    tokens = bert_tokenizer(parsed)
    logging.info("Tokens: {}".format(tokens))
    token_ids = bert_tokenizer.convert_tokens_to_ids(tokens)
    valid_length = len(token_ids)
    segment_ids = mx.nd.zeros([1, valid_length])

    output = bert_classifier(mx.nd.array([token_ids]), 
                             segment_ids, 
                             mx.nd.array([valid_length]).astype('float32'))
    response_body = json.dumps(output.asnumpy().tolist()[0])
    return response_body, output_content_type
