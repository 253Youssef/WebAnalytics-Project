from __future__ import absolute_import, division, print_function, unicode_literals

import tensorflow as tf
tf.enable_eager_execution()

import numpy as np
import os
import time
import re


def filterInput(input_string):
    return input_string

def generate_text_function(input_string, start_string, length):
  
  text = filterInput(input_string)

  vocab = sorted(set(text))

  # Creating a mapping from unique characters to indices
  char2idx = {u:i for i, u in enumerate(vocab)}
  idx2char = np.array(vocab)

  text_as_int = np.array([char2idx[c] for c in text])

  # The maximum length sentence we want for a single input in characters
  seq_length = 100
  examples_per_epoch = len(text)//seq_length

  # Create training examples / targets
  char_dataset = tf.data.Dataset.from_tensor_slices(text_as_int)

  sequences = char_dataset.batch(seq_length+1, drop_remainder=True)

  def split_input_target(chunk):
      input_text = chunk[:-1]
      target_text = chunk[1:]
      return input_text, target_text

  dataset = sequences.map(split_input_target)

  # Batch size
  BATCH_SIZE = 32
  steps_per_epoch = examples_per_epoch//BATCH_SIZE
  BUFFER_SIZE = 10000

  dataset = dataset.shuffle(BUFFER_SIZE).batch(BATCH_SIZE, drop_remainder=True)

  # Length of the vocabulary in chars
  vocab_size = len(vocab)

  # The embedding dimension
  embedding_dim = 256

  # Number of RNN units
  rnn_units = 1024

  if tf.test.is_gpu_available():
    rnn = tf.keras.layers.CuDNNGRU
  else:
    import functools
    rnn = functools.partial(
      tf.keras.layers.GRU, recurrent_activation='sigmoid')

  def build_model(vocab_size, embedding_dim, rnn_units, batch_size):
    model = tf.keras.Sequential([
      tf.keras.layers.Embedding(vocab_size, embedding_dim,
                                batch_input_shape=[batch_size, None]),
      rnn(rnn_units,
          return_sequences=True,
          recurrent_initializer='glorot_uniform',
          stateful=True),
      tf.keras.layers.Dense(vocab_size)
    ])
    return model

  model = build_model(
    vocab_size = len(vocab),
    embedding_dim=embedding_dim,
    rnn_units=rnn_units,
    batch_size=BATCH_SIZE)

  for input_example_batch, target_example_batch in dataset.take(1):
    example_batch_predictions = model(input_example_batch)

  sampled_indices = tf.random.multinomial(example_batch_predictions[0], num_samples=1)
  sampled_indices = tf.squeeze(sampled_indices,axis=-1).numpy()


  def loss(labels, logits):
    return tf.keras.losses.sparse_categorical_crossentropy(labels, logits)

  example_batch_loss  = loss(target_example_batch, example_batch_predictions)

  model.compile(
      optimizer = tf.train.AdamOptimizer(),
      loss = loss)

  # Directory where the checkpoints will be saved
  checkpoint_dir = './training_checkpoints'
  # Name of the checkpoint files
  checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}")

  checkpoint_callback=tf.keras.callbacks.ModelCheckpoint(
      filepath=checkpoint_prefix,
      save_weights_only=True)

  optimizer = tf.train.AdamOptimizer()

  # Training step
  EPOCHS = 10

  loss = 0

  for epoch in range(EPOCHS):
      start = time.time()

      # initializing the hidden state at the start of every epoch
      # initally hidden is None
      hidden = model.reset_states()

      for (batch_n, (inp, target)) in enumerate(dataset):
            with tf.GradientTape() as tape:
                # feeding the hidden state back into the model
                # This is the interesting step
                predictions = model(inp)
                loss = tf.losses.sparse_softmax_cross_entropy(target, predictions)

            grads = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))

            if batch_n % 100 == 0:
                template = 'Epoch {} Batch {} Loss {:.4f}'
                print(template.format(epoch+1, batch_n, loss))

      # saving (checkpoint) the model every 5 epochs
      if (epoch + 1) % 5 == 0:
        model.save_weights(checkpoint_prefix.format(epoch=epoch))

      print ('Epoch {} Loss {:.4f}'.format(epoch+1, loss))
      print ('Time taken for 1 epoch {} sec\n'.format(time.time() - start))

  model.save_weights(checkpoint_prefix.format(epoch=epoch))

  tf.train.latest_checkpoint(checkpoint_dir)

  model = build_model(vocab_size, embedding_dim, rnn_units, batch_size=1)

  model.load_weights(tf.train.latest_checkpoint(checkpoint_dir))

  model.build(tf.TensorShape([1, None]))

  train_perplexity = tf.exp(loss)

  def generate_text(model, start_string):
    # Evaluation step (generating text using the learned model)

    # Number of characters to generate
    num_generate = length

    # Converting our start string to numbers (vectorizing)
    input_eval = [char2idx[s] for s in start_string]
    input_eval = tf.expand_dims(input_eval, 0)

    # Empty string to store our results
    text_generated = []

    # Low temperatures results in more predictable text.
    # Higher temperatures results in more surprising text.
    # Experiment to find the best setting.
    temperature = 1.0

    # Here batch size == 1
    model.reset_states()
    for i in range(num_generate):
        predictions = model(input_eval)
        # remove the batch dimension
        predictions = tf.squeeze(predictions, 0)

        # using a multinomial distribution to predict the word returned by the model
        predictions = predictions / temperature
        predicted_id = tf.multinomial(predictions, num_samples=1)[-1,0].numpy()

        # We pass the predicted word as the next input to the model
        # along with the previous hidden state
        input_eval = tf.expand_dims([predicted_id], 0)

        text_generated.append(idx2char[predicted_id])

    return (start_string + ''.join(text_generated))

  text_list = []
  for _ in range(10):
    generated = generate_text(model, start_string=start_string)
    generated_filtered = generated.replace('\\n', ' ')
    generated_filtered = generated_filtered.replace('\\r', ' ')
    generated_filtered = generated_filtered.replace('\\t', ' ')
    text_list.append(generated_filtered)

  return text_list, str((str(train_perplexity).split('(')[1]).split(',')[0]), str((str(loss).split('(')[1]).split(',')[0])



