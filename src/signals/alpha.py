def compute_signals(df, cfg):
    px = df["Close"].unstack("Ticker")
    # Avoid deprecated default fill_method in newer pandas
    mom = px.pct_change(20, fill_method=None)
    vol = px.pct_change(fill_method=None).rolling(20).std()
    return {"mom_20": mom.tail(1).T.squeeze(), "vol_20": vol.tail(1).T.squeeze()}
