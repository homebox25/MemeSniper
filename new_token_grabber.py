
"""
Listens for new Pump.fun token creations via PumpPortal WebSocket.
"""

import asyncio
import json
from datetime import datetime
import pandas as pd
import atexit
import datetime

import websockets

# PumpPortal WebSocket URL
WS_URL = "wss://pumpportal.fun/api/data"

JUPITER_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"
SOL_MINT = "So11111111111111111111111111111111111111112"  # Native SOL

df = pd.DataFrame(columns = ["Name", "Symbol", "Address", "Creator", "Initial Buy", "Market Cap", "Bonding Curve", "Virtual SOL", "Virtual Tokens", "Price per token", "Snipeworthy"])

def format_sol(value):
    return f"{value:.6f} SOL"


def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")


def check_liquidity(token_mint, amount_in_sol=0.01):
    amount_in_lamports = int(amount_in_sol * 1_000_000_000)  # Convert SOL to lamports

    try:
        # Simulate a buy (SOL -> Token)
        buy_resp = requests.get(JUPITER_QUOTE_URL, params={
            "inputMint": SOL_MINT,
            "outputMint": token_mint,
            "amount": amount_in_lamports,
            "slippageBps": 500
        }).json()

        out_amount = buy_resp.get("data", [{}])[0].get("outAmount", 0)

        if not out_amount:
            print("Token not buyable with Jupiter.")
            return False

        # Simulate a sell (Token -> SOL)
        sell_resp = requests.get(JUPITER_QUOTE_URL, params={
            "inputMint": token_mint,
            "outputMint": SOL_MINT,
            "amount": out_amount,
            "slippageBps": 500
        }).json()

        in_amount = sell_resp.get("data", [{}])[0].get("outAmount", 0)

        # Round-trip analysis
        sol_received = in_amount / 1_000_000_000
        loss = amount_in_sol - sol_received
        loss_pct = (loss / amount_in_sol) * 100

        print(f"Buy {amount_in_sol} SOL → {out_amount} tokens → Sell = {sol_received:.6f} SOL (Loss: {loss_pct:.2f}%)")

        if loss_pct < 20:
            print("Liquidity OK.")
            return True
        else:
            print("Too much slippage — poor liquidity.")
            return False

    except Exception as e:
        print(f"Error checking liquidity: {e}")
        return False

def is_promising_token(token_info):
    try:
        market_cap = token_info.get("marketCapSol", 0)
        v_sol = token_info.get("vSolInBondingCurve", 0)
        v_tokens = token_info.get("vTokensInBondingCurve", 0)
        initial_buy = token_info.get("initialBuy", 0)

        return (
            market_cap >= 2.0 and
            v_sol >= 2.0 and
            v_tokens < 1_000_000_000 and
            initial_buy < 100
        )
    except Exception as e:
        print(f"Filter error: {e}")
        return False

async def listen_for_new_tokens():
    async with websockets.connect(WS_URL) as websocket:
        # Subscribe to new token events
        await websocket.send(json.dumps({"method": "subscribeNewToken", "params": []}))

        print("Listening for new token creations...")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if "method" in data and data["method"] == "newToken":
                    token_info = data.get("params", [{}])[0]
                elif "signature" in data and "mint" in data:
                    token_info = data
                else:
                    continue


                print("\n" + "=" * 50)
                print(
                    f"New token created: {token_info.get('name')} ({token_info.get('symbol')}) {datetime.datetime.now()}"
                )
                print("=" * 50)
                print(f"Address:        {token_info.get('mint')}")
                print(f"Creator:        {token_info.get('traderPublicKey')}")
                print(f"Initial Buy:    {format_sol(token_info.get('initialBuy', 0) / 1000000000)}")
                print(
                    f"Market Cap:     {format_sol(token_info.get('marketCapSol', 0))}"
                )
                print(f"Bonding Curve:  {token_info.get('bondingCurveKey')}")
                print(
                    f"Virtual SOL:    {format_sol(token_info.get('vSolInBondingCurve', 0))}"
                )
                print(
                    f"Virtual Tokens: {token_info.get('vTokensInBondingCurve', 0):,.0f}"
                )
                print(f"Metadata URI:   {token_info.get('uri')}")
                print(f"Signature:      {token_info.get('signature')}")
                print(f"Price per token:      {token_info.get('vSolInBondingCurve', 0) / token_info.get('vTokensInBondingCurve', 0)}")
                print(f"View: https://solscan.io/token/{token_info.get('mint')}")

             
                snipeworthy = "No"
                if ((token_info.get('initialBuy', 0) / 1000000000) >= 0.5 and (token_info.get('marketCapSol', 0) / 1000000000) >= 2 and (token_info.get('vSolInBondingCurve', 0) / 1000000000) >= 1):
                    print(f"🔥 Potential snipe-worthy token!")
                    snipeworth = "Yes"
                      

                
                print("=" * 50)

                if is_promising_token(token_info):
                    import pdb;
                    pdb.set_trace()
     
                #"Name", "Symbol", "Address", "Creator", "Initial Buy", "Market Cap", "Bonding Curve", "Virtual SOL", "Virtual Tokens", "Price per token"
    
                new_row = [token_info.get('name'), token_info.get('symbol'), token_info.get('mint'), token_info.get('traderPublicKey'), format_sol(token_info.get('initialBuy', 0)), format_sol(token_info.get('marketCapSol', 0)), token_info.get('bondingCurveKey'), token_info.get('vTokensInBondingCurve', 0), token_info.get('vSolInBondingCurve', 0), token_info.get('vSolInBondingCurve', 0) / token_info.get('vTokensInBondingCurve', 0), snipeworthy]
                df.loc[len(df)] = new_row
                save_dataframe(df)

            except websockets.exceptions.ConnectionClosed:
                print("\nWebSocket connection closed. Reconnecting...")
                break
            except json.JSONDecodeError:
                print(f"\nReceived non-JSON message: {message}")
            except Exception as e:
                print(f"\nAn error occurred: {e}")

def save_dataframe(df):
    df.to_csv("C:\\Users\\alfuc\\Desktop\\memes.csv")



async def main():
    while True:
        try:
            await listen_for_new_tokens()
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
