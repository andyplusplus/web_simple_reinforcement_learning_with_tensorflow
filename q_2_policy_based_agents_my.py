"""
* [Simple Reinforcement Learning with Tensorflow: Part 2 - Policy-based Agents](https://medium.com/@awjuliani/super-simple-reinforcement-learning-tutorial-part-2-ded33892c724)
* [github](https://github.com/awjuliani/DeepRL-Agents/blob/master/Vanilla-Policy.ipynb)
* [Getting Started with Gym](https://gym.openai.com/docs/)
"""

import tensorflow as tf
import tensorflow.contrib.slim as slim
import numpy as np
import gym
import matplotlib.pyplot as plt
# from my_utility import get_log_dir
import my_utility as utility

#######################################################################
try:
    xrange = xrange
except:
    xrange = range

env = gym.make('CartPole-v0')

#######################################################################
# Policy based agent
#######################################################################
gamma_099 = 0.99

def discount_rewards(r):
    """ take 1D float array of rewards and compute discounted reward """
    discounted_r = np.zeros_like(r)
    running_add = 0
    for t in reversed(xrange(0, r.size)):
        running_add = running_add * gamma_099 + r[t]
        discounted_r[t] = running_add
    return discounted_r



class agent():
    def __init__(self, lr, s_size_4, a_size_2, h_size_8): # (lr=1e-2, s_size=4, a_size=2, h_size_512=8)
        # These lines established the feed-forward part of the network. The agent takes a state and produces an action.
        self.state_in_x4 = tf.placeholder(shape=[None, s_size_4], dtype=tf.float32) #(?, 4)  #############################
        hidden_x8 = slim.fully_connected(self.state_in_x4, h_size_8, biases_initializer=None, activation_fn=tf.nn.relu)
        self.output_x2 = slim.fully_connected(hidden_x8, a_size_2, activation_fn=tf.nn.softmax, biases_initializer=None)
        self.chosen_action = tf.argmax(self.output_x2, 1)

        # The next six lines establish the training procedure. We feed the reward and chosen action into the network
        # to compute the loss, and use it to update the network.
        self.reward_holder = tf.placeholder(shape=[None], dtype=tf.float32)  #############################
        self.action_holder = tf.placeholder(shape=[None], dtype=tf.int32)  #############################

        #number of output elements + action_holder
        self.indexes = tf.range(0, tf.shape(self.output_x2)[0]) * tf.shape(self.output_x2)[1] + self.action_holder
        self.responsible_outputs = tf.gather(tf.reshape(self.output_x2, [-1]), self.indexes)

        self.loss = -tf.reduce_mean(tf.log(self.responsible_outputs) * self.reward_holder)

        tvars = tf.trainable_variables()
        self.gradient_holders = []
        for idx, var in enumerate(tvars):
            placeholder = tf.placeholder(tf.float32, name=str(idx) + '_holder')  #############################
            self.gradient_holders.append(placeholder)

        self.gradients = tf.gradients(self.loss, tvars)

        optimizer = tf.train.AdamOptimizer(learning_rate=lr)
        self.update_batch = optimizer.apply_gradients(zip(self.gradient_holders, tvars))



#######################################################################
# Training the agent
#######################################################################

tf.reset_default_graph()  # Clear the Tensorflow graph.


myAgent = agent(lr=1e-2, s_size_4=4, a_size_2=2, h_size_8=8)  # Load the agent.

# total_episodes_5k = utility.get_episode_restriction(5000)
# Set total number of episodes to train agent on.
# max_ep_1k = utility.get_episode_restriction(999)
total_episodes_5k = 5000  # Set total number of episodes to train agent on.
max_ep_1k = 999
update_frequency_5 = 5

init = tf.global_variables_initializer()

log_dir = utility.get_log_dir("q2")
summary_writer = tf.summary.FileWriter(log_dir, tf.get_default_graph())
summary_writer.close()


# Launch the tensorflow graph
with tf.Session() as sess:
    sess.run(init)
    total_reward = []
    total_length = []

    gradBuffer = sess.run(tf.trainable_variables()) # (4,8),(8,2)
    for ix, grad in enumerate(gradBuffer):   #init all grad to zerp
        gradBuffer[ix] = grad * 0

    for i in range(total_episodes_5k):
        s = env.reset()
        running_reward = 0
        ep_history = []  # history of all episodes, [s, a, r, s1]
        for j in range(max_ep_1k):
            # Probabilistically pick an action given our network outputs, select action according to the neural network
            a_dist = sess.run(myAgent.output_x2, feed_dict={myAgent.state_in_x4: [s]})
            a = np.random.choice(a_dist[0], p=a_dist[0])
            a = np.argmax(a_dist == a)
            # run the action, ... and add to the ep_history
            s1, r, is_done, _ = env.step(a)  # Get our reward for taking an action given a bandit.
            ep_history.append([s, a, r, s1])
            running_reward += r
            s = s1

            if is_done == True:
                # Update the network.
                ep_history = np.array(ep_history)
                ep_history[:, 2] = discount_rewards(ep_history[:, 2])

                feed_dict = {myAgent.reward_holder: ep_history[:, 2],
                             myAgent.action_holder: ep_history[:, 1],
                             myAgent.state_in_x4: np.vstack(ep_history[:, 0])}

                grads = sess.run(myAgent.gradients, feed_dict=feed_dict)
                for idx, grad in enumerate(grads):
                    gradBuffer[idx] += grad

                if i % update_frequency_5 == 0 and i != 0: # update batch every five steps
                    feed_dict = dictionary = dict(zip(myAgent.gradient_holders, gradBuffer))
                    _ = sess.run(myAgent.update_batch, feed_dict=feed_dict)
                    for ix, grad in enumerate(gradBuffer):
                        gradBuffer[ix] = grad * 0

                total_reward.append(running_reward)
                total_length.append(j)
                break

            # Update our running tally of scores.
        if i % 100 == 0:
            print(np.mean(total_reward[-100:]))

"""

16.0
21.47
25.57
38.03
43.59
53.05
67.38
90.44
120.19
131.75
162.65
156.48
168.18
181.43

"""

##################################################
##################################################
