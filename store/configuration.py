from datetime import timedelta
import os
from web3 import Web3, HTTPProvider


def readFile(p):
    with open(p, "r") as f:
        return f.read()


web3 = Web3(HTTPProvider("http://blockchain:8545"))
owner = web3.eth.accounts[0]
bytecode = readFile("./solidity/output/Payment.bin")
abi = readFile("./solidity/output//Payment.abi")
paymentContract = web3.eth.contract(bytecode=bytecode, abi=abi)


class Configuration:
    DATABASE_URL = os.environ["DATABASE_URL"] if "DATABASE_URL" in os.environ else "localhost"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{DATABASE_URL}/store"
    JWT_SECRET_KEY = "JWT_SECRET_DEV_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
