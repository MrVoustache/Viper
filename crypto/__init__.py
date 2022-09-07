try:
    import cryptography.hazmat
except ModuleNotFoundError:
    raise ModuleNotFoundError("The Viper.crypto package requires the cryptography package. Get it using 'pip install cryptography'.")