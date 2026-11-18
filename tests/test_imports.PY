# test_imports.py
import ccxt
import yfinance
import pandas as pd
import pandas_ta as ta  # ou import ta si vous avez choisi l'alternative
from langchain_ollama import ChatOllama
import requests

print("✅ Toutes les librairies sont installées correctement !")
print(f"ccxt version: {ccxt.__version__}")
print(f"pandas version: {pd.__version__}")
print(f"pandas-ta version: {ta.__version__}")
print(f"langchain-ollama version: {ChatOllama.__version__}")
print(f"requests version: {requests.__version__}")