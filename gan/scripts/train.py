"""
    Import Libraries
"""
import numpy as np
import matplotlib.pyplot as plt

from keras.layers import Dense, Dropout, Input
from keras.models import Model,Sequential
from keras.datasets import mnist

from tqdm import tqdm
from keras.layers.activation import LeakyReLU
from keras.optimizers import Adam


# Import date and stringify it for the folder name.
from datetime import datetime

date = datetime.now()
date = date.strftime("%Y_%m_%d_%H_%M_%S")

import os
os.makedirs('../images/' + date)


def load_data():
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train = (x_train.astype('float32') - 127.5) / 227.5

    x_train = x_train.reshape(60000, 784)
    return x_train, y_train, x_test, y_test


def adam_optimizer():
    return Adam(learning_rate=0.0002, beta_1=0.5)


def create_generator():
    generator = Sequential()
    generator.add(Dense(units=128, input_dim=100))
    generator.add(LeakyReLU(0.2))

    generator.add(Dense(units=128))
    generator.add(LeakyReLU(0.2))

    generator.add(Dense(units=784, activation='tanh'))

    generator.compile(loss='binary_crossentropy', optimizer=adam_optimizer())
    return generator


def create_discriminator():
    discriminator = Sequential()
    discriminator.add(Dense(units=128, input_dim=784))
    discriminator.add(LeakyReLU(0.2))
    discriminator.add(Dropout(0.3))

    discriminator.add(Dense(units=128))
    discriminator.add(LeakyReLU(0.2))

    discriminator.add(Dense(units=1, activation='sigmoid'))

    discriminator.compile(loss='binary_crossentropy', optimizer=adam_optimizer())
    return discriminator


def create_gan(discriminator, generator):
    discriminator.trainable = False
    gan_input = Input(shape=(100,))
    x = generator(gan_input)
    gan_output = discriminator(x)
    gan = Model(inputs=gan_input, outputs=gan_output)
    gan.compile(loss='binary_crossentropy', optimizer='adam')
    return gan


def plot_generated_images(epoch, generator, examples=100, dim=(10,10), figsize=(10,10)):
    noise = np.random.normal(loc=0, scale=1, size=[examples, 100])
    generated_images = generator.predict(noise)
    generated_images = generated_images.reshape(100, 28, 28)
    plt.figure(figsize=figsize)

    for i in range(generated_images.shape[0]):
        plt.subplot(dim[0], dim[1], i + 1)
        plt.imshow(generated_images[i], interpolation='nearest')
        plt.axis('off')

    plt.tight_layout()
    plt.savefig('../images/' + date +'/gan_generated_image_%d.png' % epoch)


def training(epochs=1, batch_size=128):
    # Loading the data
    (X_train, y_train, X_test, y_test) = load_data()
    batch_count = X_train.shape[0] / batch_size

    # Creating GAN
    generator = create_generator()
    discriminator = create_discriminator()
    gan = create_gan(discriminator, generator)


    diss_loss = []
    gan_loss = []
    epoch_counter = [i for i in range(epochs)]

    for e in range(1, epochs + 1):
        print("Epoch %d" % e)

        ganloss = 0
        dissloss = 0

        for _ in tqdm(range(batch_size)):
            # generate random noise as an input to initialize the generator
            noise = np.random.normal(0, 1, [batch_size, 100])

            # Generate fake MNIST images from noised input
            generated_images = generator.predict(noise)

            # Get a random set of real images
            image_batch = X_train[np.random.randint(low=0, high=X_train.shape[0], size=batch_size)]

            # Construct different batches of real and fake data
            X = np.concatenate([image_batch, generated_images])

            # Labels for generated and real data
            y_dis = np.zeros(2 * batch_size)
            y_dis[:batch_size] = 1

            # Pre-train discriminator on fake and real data before starting the gan.
            discriminator.trainable = True
            dissloss = discriminator.train_on_batch(X, y_dis)

            # Tricking the noised input of the Generator as real data
            noise = np.random.normal(0, 1, [batch_size, 100])
            y_gen = np.ones(batch_size)

            # During the training of gan, the weights of discriminator should be fixed.
            # We can enforce that by setting the trainable flag
            discriminator.trainable = False

            # training the GAN by alternating the training of the Discriminator
            # and training the chained GAN model with Discriminator’s weights freezed.
            ganloss = gan.train_on_batch(noise, y_gen)

        gan_loss.append(ganloss)
        diss_loss.append(dissloss)

        # Plot generated images.
        if e == 1 or e % 20 == 0:
            plot_generated_images(e, generator)

    return gan_loss, diss_loss, epoch_counter



def main():
    # Load the data.
    (X_train, y_train, X_test, y_test) = load_data()

    print("X Train Shape:", X_train.shape)
    print("Y Train Shape:", y_train.shape)
    print("X Test Shape:",  X_test.shape)
    print("Y Test Shape:",  y_test.shape)

    # Create the generator.
    generator = create_generator()
    generator.summary()

    # Create the discriminator.
    discriminator = create_discriminator()
    discriminator.summary()

    # Check training shape of the network.
    print(X_train.shape)

    # Create the gan.
    gan = create_gan(discriminator, generator)
    gan.summary()

    # Start training.
    (gan_loss, diss_loss, epoch_counter) = training(200, 128)

    plt.figure(figsize=(8, 6))
    plt.plot(epoch_counter, gan_loss, label="GAN Loss", marker="o")
    plt.plot(epoch_counter, diss_loss, label="Discriminator Loss", marker="s")
    plt.title("Loss vs. Epoch")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    main()