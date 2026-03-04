import os
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# --------------------------
# PARAMETERS
# --------------------------
IMG_SIZE = 224
BATCH_SIZE = 4
EPOCHS = 30
DATASET_PATH = r"D:\app_connect_dashboard\data (1)\data"

# --------------------------
# DATA CHECKPOINT
# --------------------------
# ❗ Make sure the directory contains 4 class folders like:
# C:\Users\hp\OneDrive\Desktop\AIML\data (1)\Organic
# C:\Users\hp\OneDrive\Desktop\AIML\data (1)\Plastic
# C:\Users\hp\OneDrive\Desktop\AIML\data (1)\Recyclable
# C:\Users\hp\OneDrive\Desktop\AIML\data (1)\Non-Recyclable

# --------------------------
# DATA PREPROCESSING
# --------------------------
datagen = ImageDataGenerator(
    rescale=1. / 255,
    validation_split=0.2,
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

train_data = datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',  # one-hot encoded labels
    subset='training',
    shuffle=True
)

val_data = datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=True
)

print("✅ Class indices:", train_data.class_indices)
num_classes = len(train_data.class_indices)

# --------------------------
# MODEL BUILDING (MobileNetV2)
# --------------------------
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(IMG_SIZE, IMG_SIZE, 3))
base_model.trainable = False

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.4)(x)
predictions = Dense(num_classes, activation='softmax')(x)  # dynamically use number of classes

model = Model(inputs=base_model.input, outputs=predictions)

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# --------------------------
# CALLBACKS
# --------------------------
early_stop = EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True)
checkpoint = ModelCheckpoint("model.keras", monitor='val_accuracy', save_best_only=True)

# --------------------------
# TRAINING
# --------------------------
history = model.fit(
    train_data,
    validation_data=val_data,
    epochs=EPOCHS,
    callbacks=[early_stop, checkpoint]
)

# --------------------------
# TRAINING SUMMARY
# --------------------------
final_train_acc = history.history['accuracy'][-1]
final_val_acc = history.history['val_accuracy'][-1]
epochs_run = len(history.history['accuracy'])

print(f"\n✅ Model Training Summary:")
print(f"Total Epochs Trained: {epochs_run}")
print(f"Final Training Accuracy: {final_train_acc:.4f}")
print(f"Final Validation Accuracy: {final_val_acc:.4f}")

# --------------------------
# VISUALIZATION
# --------------------------
plt.figure(figsize=(12, 6))
plt.plot(history.history['accuracy'], label='Train Acc')
plt.plot(history.history['val_accuracy'], label='Val Acc')
plt.title('Accuracy per Epoch')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("accuracy_plot.png")
plt.show()
