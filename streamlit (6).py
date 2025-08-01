# -*- coding: utf-8 -*-
"""Streamlit.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1xCA_4aDMFHwrQ4mfaWib-I_aJDdZtZ9a
"""

# Core libraries for data handling and numerical operations
import pandas as pd
import numpy as np

# Preprocessing tools from scikit-learn
from sklearn.model_selection import train_test_split # For splitting data into training/testing sets
from sklearn.preprocessing import LabelEncoder, StandardScaler, label_binarize # For encoding categorical labels and scaling numerical features

# Machine learning models from scikit-learn
from sklearn.ensemble import RandomForestClassifier # A powerful ensemble model
from sklearn.svm import SVC # Support Vector Classifier
from sklearn.linear_model import LogisticRegression # A linear classification model
# import xgboost as xgb # Uncomment and install if you want to use XGBoost

# Evaluation metrics and plotting tools
from sklearn.metrics import accuracy_score, precision_score, confusion_matrix, roc_curve, auc
import matplotlib.pyplot as plt # For creating plots
import seaborn as sns # For making plots visually appealing

# For saving and loading models
import joblib

# Load the dataset from the CSV file
df = pd.read_csv('market_pipe_thickness_loss_dataset.csv')

# Display the first few rows to understand its structure
print("Original Dataset Head:")
print(df.head())

# Display general information about the dataset (data types, non-null counts)
print("\nDataset Info:")
df.info()

# Check the unique values in the target 'Condition' column
print("\nUnique Conditions (Target Variable):")
print(df['Condition'].unique())

# Define features (X) and target (y)
# 'Condition' is our target variable
target_feature = 'Condition'

# Identify numerical features that will be scaled
numerical_features = ['Pipe_Size_mm', 'Thickness_mm', 'Max_Pressure_psi', 'Temperature_C',
                      'Corrosion_Impact_Percent', 'Thickness_Loss_mm', 'Material_Loss_Percent', 'Time_Years']

# Identify categorical features that will be one-hot encoded
categorical_features = ['Material', 'Grade']

# --- 2.1 One-Hot Encode Categorical Features ---
# Convert categorical text data into numerical format using one-hot encoding.
# drop_first=True prevents multicollinearity by dropping one category from each feature.
df_encoded = pd.get_dummies(df, columns=categorical_features, drop_first=True)

print("\nDataset after One-Hot Encoding Head:")
print(df_encoded.head())

# --- 2.2 Encode the Target Variable ---
# Convert the 'Condition' labels ('Normal', 'Moderate', 'Critical') into numerical values (0, 1, 2).
# This is necessary for classification models.
le = LabelEncoder()
df_encoded[target_feature + '_encoded'] = le.fit_transform(df_encoded[target_feature])

# Display the mapping from encoded numbers back to original labels
print("\nTarget Variable Mapping:")
for i, name in enumerate(le.classes_):
    print(f"{i}: {name}")

# Separate features (X) and the encoded target (y)
X = df_encoded.drop([target_feature, target_feature + '_encoded'], axis=1) # Drop original and encoded target columns from features
y = df_encoded[target_feature + '_encoded'] # Our numerical target variable

# --- 2.3 Feature Scaling ---
# Initialize the StandardScaler. This will transform numerical features to have a mean of 0 and a standard deviation of 1.
# Scaling is crucial for models like SVC and Logistic Regression, and can benefit RandomForest as well.
scaler = StandardScaler()

# Select only the numerical columns that are still present in X after one-hot encoding
# (original categorical columns are now replaced by dummy variables)
# We make sure to only scale columns that were originally numerical.
numerical_cols_after_encoding = [col for col in X.columns if col in numerical_features]

# Apply scaling to the identified numerical features in the DataFrame X
X[numerical_cols_after_encoding] = scaler.fit_transform(X[numerical_cols_after_encoding])

print("\nFeatures (X) after Scaling and One-Hot Encoding Head:")
print(X.head())
print("\nTarget (y) Head:")
print(y.head())

# Split the dataset into training and testing sets.
# test_size=0.3 means 30% of the data will be used for testing, 70% for training.
# random_state=42 ensures reproducibility (you'll get the same split every time).
# stratify=y ensures that the proportion of each class in y is maintained in both training and testing sets.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

print(f"\nTraining set size: {X_train.shape[0]} samples")
print(f"Testing set size: {X_test.shape[0]} samples")

# Get class names for plotting (using the LabelEncoder fitted earlier)
class_names = le.classes_
n_classes = len(class_names) # Number of unique classes

# --- Function to evaluate and plot model results ---
def evaluate_model(model, X_test, y_test, class_names, n_classes, model_name):
    """
    Trains a given model, makes predictions, calculates accuracy and precision,
    and plots confusion matrix and ROC curve.
    """
    print(f"\n--- Evaluating {model_name} ---")

    # Make predictions on the test set
    y_pred = model.predict(X_test)

    # Calculate Accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")

    # Calculate Precision (using 'weighted' for multi-class)
    # Precision is the ratio of correctly predicted positive observations to the total predicted positives.
    # 'weighted' takes into account class imbalance by computing the average of binary precision
    # in an average weighted by the number of true instances for each label.
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    print(f"Precision: {precision:.4f}")

    # --- Confusion Matrix Plot ---
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title(f'Confusion Matrix - {model_name}')
    plt.tight_layout()
    plt.show() # Display the plot

    # --- ROC Curve Plot (One-vs-Rest for Multi-Class) ---
    # ROC curve requires probability predictions, so check if the model supports it.
    if hasattr(model, "predict_proba"):
        # Binarize the true labels for ROC curve calculation (one-vs-rest)
        y_test_binarized = label_binarize(y_test, classes=np.unique(y_test))
        y_pred_proba = model.predict_proba(X_test) # Get probability predictions

        plt.figure(figsize=(10, 8))
        for i in range(n_classes):
            # Calculate False Positive Rate (FPR), True Positive Rate (TPR) and thresholds for each class
            fpr, tpr, _ = roc_curve(y_test_binarized[:, i], y_pred_proba[:, i])
            # Calculate Area Under the Curve (AUC)
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, label=f'ROC curve of class {class_names[i]} (area = {roc_auc:.2f})')

        plt.plot([0, 1], [0, 1], 'k--', label='No Skill (AUC = 0.50)') # Baseline for random classifier
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'Receiver Operating Characteristic (ROC) Curve - {model_name} (One-vs-Rest)')
        plt.legend(loc='lower right')
        plt.grid(True)
        plt.tight_layout()
        plt.show() # Display the plot
    else:
        print(f"Note: {model_name} does not have predict_proba method for ROC curve (e.g., SVC needs probability=True).")

    return accuracy, precision

# Dictionary to store model accuracies and precisions for comparison
model_performance = {}

# --- 5.1 RandomForestClassifier ---
print("\n--- Training Random Forest Classifier ---")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train) # Train the model
rf_accuracy, rf_precision = evaluate_model(rf_model, X_test, y_test, class_names, n_classes, "Random Forest")
model_performance["Random Forest"] = {"Accuracy": rf_accuracy, "Precision": rf_precision}

# --- 5.2 Support Vector Machine (SVC) ---
print("\n--- Training Support Vector Machine (SVC) ---")
# SVC with 'linear' kernel is a good starting point.
# probability=True is essential for getting predict_proba for ROC curve, but can make training slower.
svc_model = SVC(kernel='linear', probability=True, random_state=42)
svc_model.fit(X_train, y_train) # Train the model
svc_accuracy, svc_precision = evaluate_model(svc_model, X_test, y_test, class_names, n_classes, "SVC")
model_performance["SVC"] = {"Accuracy": svc_accuracy, "Precision": svc_precision}

# --- 5.3 Logistic Regression ---
print("\n--- Training Logistic Regression ---")
# max_iter increased to ensure convergence, especially with scaled data.
# multi_class='auto' chooses the appropriate strategy for multi-class classification.
lr_model = LogisticRegression(max_iter=1000, random_state=42, multi_class='auto')
lr_model.fit(X_train, y_train) # Train the model
lr_accuracy, lr_precision = evaluate_model(lr_model, X_test, y_test, class_names, n_classes, "Logistic Regression")
model_performance["Logistic Regression"] = {"Accuracy": lr_accuracy, "Precision": lr_precision}

# --- 5.4 (Optional) XGBoostClassifier ---
# If you have xgboost installed, uncomment and run this section:
# try:
#     import xgboost as xgb
#     print("\n--- Training XGBoost Classifier ---")
#     # For multi-class, objective='multi:softprob' is common.
#     # use_label_encoder=False is recommended for newer XGBoost versions.
#     xgb_model = xgb.XGBClassifier(objective='multi:softprob', use_label_encoder=False, eval_metric='mlogloss', random_state=42)
#     xgb_model.fit(X_train, y_train)
#     xgb_accuracy, xgb_precision = evaluate_model(xgb_model, X_test, y_test, class_names, n_classes, "XGBoost")
#     model_performance["XGBoost"] = {"Accuracy": xgb_accuracy, "Precision": xgb_precision}
# except ImportError:
#     print("\nXGBoost not installed. Skipping XGBoost evaluation.")

print("\n--- Model Performance Summary ---")
performance_df = pd.DataFrame.from_dict(model_performance, orient='index')
print(performance_df)

# Find the model with the highest accuracy
best_model_name = performance_df['Accuracy'].idxmax()
print(f"\nBest model based on Accuracy: {best_model_name} (Accuracy: {performance_df.loc[best_model_name]['Accuracy']:.4f})")

# If multiple models have the same highest accuracy, you might then choose based on precision, or other factors.
# For simplicity, we'll stick with the one with highest accuracy.
if best_model_name == "Random Forest":
    best_model = rf_model
elif best_model_name == "SVC":
    best_model = svc_model
elif best_model_name == "Logistic Regression":
    best_model = lr_model
# elif best_model_name == "XGBoost": # Uncomment if XGBoost was evaluated
#     best_model = xgb_model
else:
    best_model = None # Fallback

print(f"Selected best model object: {best_model}")

# --- 7.1 Save the Best Model ---
if best_model is not None:
    model_filename = 'pipeline_condition_classifier.joblib'
    joblib.dump(best_model, model_filename)
    print(f"\nBest model ({best_model_name}) saved as '{model_filename}'")
else:
    print("\nNo best model selected to save.")

# --- 7.2 Save the Scaler ---
scaler_filename = 'scaler.joblib'
joblib.dump(scaler, scaler_filename)
print(f"Scaler saved as '{scaler_filename}'")

# --- 7.3 Save the Label Encoder ---
label_encoder_filename = 'label_encoder.joblib'
joblib.dump(le, label_encoder_filename)
print(f"Label Encoder saved as '{label_encoder_filename}'")

print("\nMachine learning pipeline setup complete. You can now use the saved files in your web application.")

# --- Add these lines to your ML training script (e.g., in your Colab notebook) ---
import joblib
# Assuming 'X' is your final features DataFrame after all preprocessing
model_features_order_saved = X.columns.tolist()
joblib.dump(model_features_order_saved, 'model_features_order.joblib')
print("Model feature order saved as 'model_features_order.joblib'")
# ---------------------------------------------------------------------------------

# streamlit (1).py (or app.py)
! pip install streamlit -q
!wget -q -0 - ipv4.icanhazip.com
!streamlit run app.py & npx localtunnel --port 8501
# Import necessary libraries for Streamlit, data handling, and model loading
import streamlit as st
import pandas as pd
import joblib
import numpy as np

# --- 0. Load the original dataset within the app to correctly determine material options ---
# This is needed for the selectbox options and to get the full list of dummy column names.
try:
    original_df = pd.read_csv('market_pipe_thickness_loss_dataset.csv')
except FileNotFoundError:
    st.error("Error: 'market_pipe_thickness_loss_dataset.csv' not found. Please ensure it's in the same directory.")
    st.stop()

# --- 1. Load the Saved Machine Learning Components and Feature Order ---
# This is crucial for your web app to use the trained model and preprocessing steps.
try:
    model = joblib.load('pipeline_condition_classifier.joblib')
    scaler = joblib.load('scaler.joblib')
    label_encoder = joblib.load('label_encoder.joblib')
    # Load the exact feature order from training
    model_features_order = joblib.load('model_features_order.joblib')
    st.success("ML Model, Scaler, Label Encoder, and Feature Order loaded successfully!")
except FileNotFoundError as e:
    st.error(f"Error loading ML files: {e}. Please ensure all .joblib files and .csv are in the same directory.")
    st.stop() # Stop the app if files are not found

# --- 2. Define Features and Default Values ---
# These are the *original* numerical and categorical features for reference,
# not directly used for defining model_features_order now that it's loaded.
numerical_features_for_model = ['Pipe_Size_mm', 'Thickness_mm', 'Max_Pressure_psi', 'Temperature_C',
                                'Corrosion_Impact_Percent', 'Thickness_Loss_mm', 'Material_Loss_Percent', 'Time_Years']
categorical_features_original = ['Material', 'Grade'] # Used for one-hot encoding logic later


# --- Default values for features removed from user input ---
DEFAULT_CORROSION_IMPACT_PERCENT = 15.0 # Example: using an average or typical value if not provided by user
# The default grade is handled implicitly by setting all Grade_dummy_columns to 0.


# --- 3. Streamlit App Layout and Styling (Wow Factor!) ---

# Set wide mode for the page
st.set_page_config(layout="wide", page_title="Pipeline Integrity Predictor", page_icon="⚙️")

# Custom CSS for a more appealing and interactive look
st.markdown(
    """
    <style>
    .main {
        background-color: #f0f2f6;
        padding: 20px;
    }
    .st-emotion-cache-vk33v5 { /* Target the header/title element to center it */
        text-align: center;
        color: #2c3e50;
    }
    .st-emotion-cache-vk33v5 h1 {
        font-size: 3.5em;
        margin-bottom: 0.5em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .st-emotion-cache-vk33v5 h2 {
        color: #34495e;
        font-size: 1.8em;
        margin-bottom: 1em;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        font-size: 1.1em;
        transition: all 0.3s ease;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .stButton>button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
        box-shadow: 4px 4px 8px rgba(0,0,0,0.3);
    }
    .prediction-box {
        background-color: #ffffff;
        border-left: 8px solid #3498db;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .prediction-box h3 {
        color: #2c3e50;
        margin-bottom: 15px;
        font-size: 1.6em;
    }
    .prediction-box p {
        font-size: 1.2em;
        margin-bottom: 8px;
        color: #34495e;
    }
    .prediction-box .highlight {
        font-weight: bold;
        color: #e74c3c; /* Critical */
    }
    .prediction-box .moderate {
        font-weight: bold;
        color: #f39c12; /* Moderate */
    }
    .prediction-box .normal {
        font-weight: bold;
        color: #27ae60; /* Normal */
    }
    .sidebar .sidebar-content {
        background-color: #ecf0f1;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.1);
    }
    .stSlider > div > div > div { /* Make sliders more prominent */
        background-color: #3498db;
    }
    .stSlider [data-baseweb="slider"] {
        background-color: #ecf0f1;
    }
    .stSelectbox {
        background-color: #ecf0f1;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("⚙️ Pipeline Integrity Prediction App")
st.markdown("## Predict Pipeline Condition & Degradation Over Time")

st.sidebar.header("Pipeline Parameters")
st.sidebar.markdown("Adjust the values below to simulate different pipeline scenarios.")


# --- 4. User Input Collection ---
# Use Streamlit widgets for user inputs

# Row 1: Pipe Size, Thickness, Material
col1, col2 = st.sidebar.columns(2)
pipe_size = col1.slider("Pipe Size (mm)", min_value=100, max_value=2000, value=800, step=50)
initial_thickness = col2.slider("Initial Thickness (mm)", min_value=5.0, max_value=50.0, value=15.0, step=0.5)

# Dynamically get material categories from the loaded original_df
material_options = original_df['Material'].unique().tolist()
material = st.sidebar.selectbox("Material", material_options)

# Renamed 'Time (Years)' to 'Years to predict'
years_to_predict = st.sidebar.slider("Years to predict", min_value=0, max_value=30, value=10, step=1)

# Row 2: Max Pressure, Temperature
col3, col4 = st.sidebar.columns(2)
max_pressure = col3.slider("Max Pressure (psi)", min_value=100, max_value=3000, value=1000, step=50)
temperature = col4.slider("Temperature (°C)", min_value=-10.0, max_value=100.0, value=25.0, step=0.5)


# --- 5. Prediction Logic ---

# Create a button to trigger prediction
if st.sidebar.button("Predict Pipeline Integrity"):
    st.markdown("---") # Visual separator

    # --- 5.1 Simple Logic for Thickness Loss and Material Loss (Illustrative) ---
    # Now using DEFAULT_CORROSION_IMPACT_PERCENT as it's no longer an input.
    # This is a placeholder for a regression model if you were to train one separately.
    corrosion_rate_per_percent_impact = 0.05 # mm loss per year per percent corrosion impact (illustrative)

    predicted_thickness_loss_mm = years_to_predict * (DEFAULT_CORROSION_IMPACT_PERCENT / 100.0) * corrosion_rate_per_percent_impact
    if predicted_thickness_loss_mm > initial_thickness * 0.95: # Cap to prevent unrealistic total loss
        predicted_thickness_loss_mm = initial_thickness * 0.95 # Cannot lose more than initial thickness

    predicted_material_loss_percent = (predicted_thickness_loss_mm / initial_thickness) * 100
    if predicted_material_loss_percent > 100: # Cap at 100%
        predicted_material_loss_percent = 100.0

    st.subheader("💡 Derived Degradation Metrics (Illustrative)")
    st.info(f"**Predicted Thickness Loss:** `{predicted_thickness_loss_mm:.2f} mm`")
    st.info(f"**Predicted Percentage Material Loss:** `{predicted_material_loss_percent:.2f}%`")
    st.caption(f"*(Note: These loss values are estimated using a simplified calculation with a default corrosion impact of {DEFAULT_CORROSION_IMPACT_PERCENT}%. For real-world accuracy, a dedicated regression model would be trained for these outputs.)*")

    # --- 5.2 Prepare Input for Classification Model ---
    # Create a Series with all the numerical features
    numerical_input_series = pd.Series({
        'Pipe_Size_mm': pipe_size,
        'Thickness_mm': initial_thickness,
        'Max_Pressure_psi': max_pressure,
        'Temperature_C': temperature,
        'Corrosion_Impact_Percent': DEFAULT_CORROSION_IMPACT_PERCENT,
        'Thickness_Loss_mm': predicted_thickness_loss_mm,
        'Material_Loss_Percent': predicted_material_loss_percent,
        'Time_Years': years_to_predict,
    })

    # Create a DataFrame with the exact columns that the model expects, initialized with 0s
    # This is crucial for matching the column order and presence.
    processed_input_df = pd.DataFrame(0.0, index=[0], columns=model_features_order)

    # Fill in numerical features
    for col in numerical_features_for_model:
        processed_input_df.loc[0, col] = numerical_input_series[col]

    # Fill in one-hot encoded 'Material' feature
    # The dummy column name is 'Material_HDPE' or 'Material_PVC'.
    # If material is 'Carbon Steel', its dummy column was dropped, so it's represented by all Material_dummies being 0.
    if material != 'Carbon Steel': # Assuming 'Carbon Steel' was dropped first for Material
        dummy_col_name = f'Material_{material}'
        # Check if the dummy column exists in the model's expected features, then set to 1
        if dummy_col_name in processed_input_df.columns:
            processed_input_df.loc[0, dummy_col_name] = 1

    # For Grade, since it's removed from user input, its dummy columns will remain 0.
    # This implicitly selects the 'dropped_first' category (e.g., 'ASTM A333 Grade 6') as the default.

    # Scale numerical features using the LOADED scaler
    processed_input_df[numerical_features_for_model] = scaler.transform(processed_input_df[numerical_features_for_model])

    # --- 5.3 Make Prediction with the Classifier ---
    prediction_encoded = model.predict(processed_input_df)[0]
    predicted_condition = label_encoder.inverse_transform([prediction_encoded])[0]

    # --- 6. Display Results (Wow Factor!) ---
    st.subheader("🎉 Predicted Pipeline Condition")
    condition_style = ""
    if predicted_condition == "Critical":
        condition_style = "highlight"
    elif predicted_condition == "Moderate":
        condition_style = "moderate"
    elif predicted_condition == "Normal":
        condition_style = "normal"

    st.markdown(f"""
        <div class="prediction-box">
            <h3>Predicted Condition: <span class="{condition_style}">{predicted_condition}</span></h3>
            <p>Based on the provided parameters and estimated degradation, the pipeline segment is predicted to be in a <span class="{condition_style}">{predicted_condition}</span> condition.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Wow Factor: Interpretation and Actionable Insights ---
    st.subheader("Next Steps & Recommendations:")
    if predicted_condition == "Critical":
        st.error("🚨 **Urgent Action Required!** This pipeline segment is in a CRITICAL condition. Immediate inspection and potential replacement or major repair are highly recommended to prevent failure and ensure safety.")
        st.markdown("Consider scheduling emergency maintenance and re-routing if possible. Further investigation (e.g., in-line inspection, NDT) is crucial.")
    elif predicted_condition == "Moderate":
        st.warning("⚠️ **Attention Needed!** This pipeline segment is in a MODERATE condition. Regular monitoring should be intensified, and a detailed inspection (e.g., within the next 6-12 months) is advised to assess the degradation rate and plan for future maintenance.")
        st.markdown("Prioritize this segment for upcoming routine inspections. Evaluate if operational adjustments can mitigate further degradation.")
    elif predicted_condition == "Normal":
        st.success("✅ **Good Condition!** This pipeline segment is in a NORMAL condition. Continue with routine monitoring and scheduled maintenance as per your standard integrity management program.")
        st.markdown("While currently stable, continuous monitoring and adherence to maintenance schedules are important to prevent future issues.")

    st.markdown("---")
    st.markdown("### How this Prediction Works:")
    st.info("""
    This application uses a pre-trained **Machine Learning Classifier** to predict the pipeline's condition.
    * **Input Derivation:** 'Thickness Loss (mm)' and 'Percentage Material Loss (%)' are estimated based on 'Years to predict' and a default corrosion impact percentage.
    * **Prediction:** These estimated loss values, along with other pipeline parameters you provide, are fed into the classifier to predict the final 'Condition'.
    """)
    st.markdown("---")
    st.markdown("Developed for your Final Year Project. Enjoy!")