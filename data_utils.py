"""
Utility functions for loading and transforming transaction data
"""
import pandas as pd
import os


def _resolve_data_file(csv_file: str) -> str:
    """Resolve transaction file path - always prefer the UPI dataset."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Always prioritize the UPI dataset
    upi_file = os.path.join(base_dir, "upi_transactions_2024 (1).csv")
    if os.path.exists(upi_file):
        return upi_file

    if csv_file and os.path.exists(csv_file):
        return csv_file

    candidate_files = [
        os.path.join(os.path.dirname(base_dir), "upi_transactions_2024 (1).csv"),
        os.path.join(base_dir, "transaction_data_new.csv"),
        os.path.join(base_dir, "transaction_logs.csv"),
    ]

    for candidate in candidate_files:
        if os.path.exists(candidate):
            return candidate

    raise FileNotFoundError("No transaction data file found")


def load_transaction_data(csv_file='upi_transactions_2024 (1).csv'):
    """
    Load transaction data from new format and transform to old format.
    Maps new columns to old column names for backward compatibility.
    
    Parameters:
    -----------
    csv_file : str
        The CSV file to load. Defaults to 'transaction_data_new.csv'
    
    Returns:
    --------
    pd.DataFrame
        Transaction data with columns:
        - transaction_time (datetime)
        - transaction_status (Success/Failure)
        - error_type, error_code, error_description
        - latency_ms
        - device_type, network_type
        - is_peak_hour (bool)
        - is_weekend (bool)
        - hour, day_of_week
    """
    resolved_file = _resolve_data_file(csv_file)

    # The UPI 2024 dataset has NO header row – supply column names explicitly
    if 'upi_transactions_2024' in os.path.basename(resolved_file):
        UPI_COLUMNS = [
            'transaction id', 'timestamp', 'transaction type', 'merchant_category',
            'amount (INR)', 'transaction_status', 'sender_age_group', 'receiver_age_group',
            'sender_state', 'sender_bank', 'receiver_bank', 'device_type',
            'network_type', 'fraud_flag', 'hour', 'day_name', 'is_weekend'
        ]
        df = pd.read_csv(resolved_file, names=UPI_COLUMNS, header=None,
                         skip_blank_lines=True, on_bad_lines='skip')
    else:
        df = pd.read_csv(resolved_file)
    
    # Check if this is the new format (has 'timestamp', 'status', 'failure_reason')
    if 'timestamp' in df.columns and 'status' in df.columns and 'failure_reason' in df.columns:
        # Transform new format to old format
        df_transformed = df.copy()
        
        # Rename columns to match old format
        df_transformed.rename(columns={
            'timestamp': 'transaction_time',
            'status': 'transaction_status',
            'failure_reason': 'error_type',
            'latency': 'latency_ms',
            'network': 'network_type',
            'device': 'device_type'
        }, inplace=True)
        
        # Convert status values to old format (SUCCESS → Success, FAILED → Failure)
        df_transformed['transaction_status'] = df_transformed['transaction_status'].replace({
            'SUCCESS': 'Success',
            'FAILED': 'Failure'
        })
        
        # Convert timestamp to datetime
        df_transformed['transaction_time'] = pd.to_datetime(df_transformed['transaction_time'])
        
        # Add error_code and error_description for failed transactions
        error_code_map = {
            'timeout': 'NET_TIMEOUT',
            'payment_error': 'PAY_FAILED',
            'auth_failed': 'AUTH_ERR',
            'server_error': 'SERVER_ERR',
            'db_error': 'DB_CONN'
        }
        
        error_description_map = {
            'timeout': 'Network Timeout',
            'payment_error': 'Payment Gateway Failure',
            'auth_failed': 'Authentication Error',
            'server_error': 'Internal Server Error',
            'db_error': 'Database Connection Failure'
        }
        
        df_transformed['error_code'] = df_transformed['error_type'].map(error_code_map)
        df_transformed['error_description'] = df_transformed['error_type'].map(error_description_map)
        
        # Fill empty error types/codes for successful transactions
        df_transformed.loc[df_transformed['transaction_status'] == 'Success', 'error_type'] = ''
        df_transformed.loc[df_transformed['transaction_status'] == 'Success', 'error_code'] = ''
        df_transformed.loc[df_transformed['transaction_status'] == 'Success', 'error_description'] = ''
        
        # Add business hour classification (9 AM - 6 PM)
        df_transformed['hour'] = df_transformed['transaction_time'].dt.hour
        df_transformed['is_peak_hour'] = (df_transformed['hour'] >= 9) & (df_transformed['hour'] < 18)
        
        # Add weekend classification (Saturday=5, Sunday=6)
        df_transformed['day_of_week'] = df_transformed['transaction_time'].dt.dayofweek
        df_transformed['is_weekend'] = df_transformed['day_of_week'].isin([5, 6])

        # Add compatibility columns for analytics engine components
        df_transformed['timestamp'] = df_transformed['transaction_time']
        df_transformed['success'] = df_transformed['transaction_status'].eq('Success')
        
        return df_transformed
    elif 'transaction id' in df.columns and 'timestamp' in df.columns and 'amount (INR)' in df.columns:
        # Transform uploaded UPI dataset format to standard format
        df_transformed = pd.DataFrame()

        # Primary fields
        df_transformed['transaction_id'] = df['transaction id']
        df_transformed['transaction_time'] = pd.to_datetime(df['timestamp'])
        df_transformed['amount'] = pd.to_numeric(df['amount (INR)'], errors='coerce').fillna(0)
        df_transformed['state'] = df.get('sender_state', 'Unknown')
        df_transformed['device_type'] = df.get('device_type', 'Unknown')
        df_transformed['network_type'] = df.get('network_type', 'Unknown')
        df_transformed['category'] = df.get('merchant_category', 'Other')
        df_transformed['fraud_flag'] = pd.to_numeric(df.get('fraud_flag', 0), errors='coerce').fillna(0).astype(int)

        # Status normalization
        status_raw = df.get('transaction_status', '').astype(str).str.upper().str.strip()
        df_transformed['transaction_status'] = status_raw.replace({
            'SUCCESS': 'Success',
            'FAILED': 'Failure',
            'FAILURE': 'Failure'
        })
        df_transformed.loc[~df_transformed['transaction_status'].isin(['Success', 'Failure']), 'transaction_status'] = 'Failure'

        # Time dimensions
        df_transformed['hour'] = df_transformed['transaction_time'].dt.hour
        df_transformed['is_peak_hour'] = (df_transformed['hour'] >= 9) & (df_transformed['hour'] < 18)
        df_transformed['day_of_week'] = df_transformed['transaction_time'].dt.dayofweek
        df_transformed['is_weekend'] = df_transformed['day_of_week'].isin([5, 6])

        # Error enrichment for failed transactions
        failed_mask = df_transformed['transaction_status'] == 'Failure'
        failed_network = df_transformed['network_type'].fillna('').astype(str).str.upper()
        failed_hour = df_transformed['hour']

        df_transformed['error_type'] = ''
        df_transformed.loc[failed_mask, 'error_type'] = 'payment_error'
        df_transformed.loc[failed_mask & failed_network.eq('3G'), 'error_type'] = 'timeout'
        df_transformed.loc[failed_mask & failed_hour.between(0, 5), 'error_type'] = 'server_error'
        df_transformed.loc[failed_mask & df_transformed['fraud_flag'].eq(1), 'error_type'] = 'auth_failed'

        error_code_map = {
            'timeout': 'NET_TIMEOUT',
            'payment_error': 'PAY_FAILED',
            'auth_failed': 'AUTH_ERR',
            'server_error': 'SERVER_ERR',
            'db_error': 'DB_CONN'
        }
        error_description_map = {
            'timeout': 'Network Timeout',
            'payment_error': 'Payment Gateway Failure',
            'auth_failed': 'Authentication Error',
            'server_error': 'Internal Server Error',
            'db_error': 'Database Connection Failure'
        }
        df_transformed['error_code'] = df_transformed['error_type'].map(error_code_map).fillna('')
        df_transformed['error_description'] = df_transformed['error_type'].map(error_description_map).fillna('')

        # Latency approximation (dataset has no latency column)
        network_base_latency = {
            '5G': 45,
            '4G': 75,
            '3G': 140,
            'WIFI': 60
        }
        network_upper = df_transformed['network_type'].fillna('').astype(str).str.upper()
        base_latency = network_upper.map(network_base_latency).fillna(90)
        amount_jitter = (df_transformed['amount'] % 35)
        failure_penalty = failed_mask.astype(int) * 180
        df_transformed['latency_ms'] = (base_latency + amount_jitter + failure_penalty).round(2)

        # Additional useful columns
        df_transformed['age_group'] = df.get('sender_age_group', '')
        df_transformed['sender_bank'] = df.get('sender_bank', 'Unknown')
        df_transformed['receiver_bank'] = df.get('receiver_bank', 'Unknown')
        df_transformed['transaction_type'] = df.get('transaction type', 'Unknown')
        df_transformed['user_id'] = 'UPI_USER_' + df.index.astype(str)

        # Compatibility columns for analytics engine components
        df_transformed['timestamp'] = df_transformed['transaction_time']
        df_transformed['success'] = df_transformed['transaction_status'].eq('Success')

        return df_transformed
    else:
        # Already in old format
        if 'transaction_time' in df.columns and 'timestamp' not in df.columns:
            df['transaction_time'] = pd.to_datetime(df['transaction_time'])
            df['timestamp'] = df['transaction_time']
        if 'transaction_status' in df.columns and 'success' not in df.columns:
            df['success'] = df['transaction_status'].eq('Success')
        return df
