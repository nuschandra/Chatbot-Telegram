import boto3
import tensorflow as tf
from tensorflow import keras
import s3fs
import h5py
from bert import BertModelLayer



# Load csv file directly into python
s3 = s3fs.S3FileSystem(key='AKIAICLTGFNXJRPY4CYA',secret='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')
f = h5py.File(s3.open("s3://virtual-recruiter-chatbot-assets/bert_intent_detection.hdf5", "rb"))
model = keras.models.load_model(f,custom_objects={"BertModelLayer": BertModelLayer},compile=False)
model.summary()
