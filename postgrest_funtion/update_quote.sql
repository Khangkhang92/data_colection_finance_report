CREATE OR REPLACE FUNCTION save_update_quote(p_data JSONB)
RETURNS VOID AS $$
DECLARE
    v_symbol_id INTEGER;
    v_date DATE;
    v_datetime TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get or create the symbol
    SELECT id INTO v_symbol_id FROM symbol WHERE ticker = p_data->>'Symbol';
    IF v_symbol_id IS NULL THEN
        INSERT INTO symbol (ticker) VALUES (p_data->>'Symbol') RETURNING id INTO v_symbol_id;
    END IF;

    -- Extract date and datetime
    v_datetime := (p_data->>'Date')::timestamp with time zone;
    v_date := v_datetime::date;

    -- Insert or update the update_quote record
    INSERT INTO update_quote (
        symbol_ticker,
        date,
        datetime,
        price_current,
        price_last,
        price_high,
        price_low,
        price_open,
        price_close,
        price_average,
        total_volume,
        volume,
        total_value,
        price_bid1,
        quantity_bid1,
        price_bid2,
        quantity_bid2,
        price_bid3,
        quantity_bid3,
        price_ask1,
        quantity_ask1,
        price_ask2,
        quantity_ask2,
        price_ask3,
        quantity_ask3,
        buy_foreign_value,
        sell_foreign_value,
        buy_foreign_quantity,
        current_foreign_room,
        total_active_buy_volume,
        total_active_sell_volume,
        price_percent_change,
        price_change
    )
    VALUES (
        p_data->>'Symbol',
        v_date,
        v_datetime,
        (p_data->>'PriceCurrent')::float,
        (p_data->>'PriceLast')::float,
        (p_data->>'PriceHigh')::float,
        (p_data->>'PriceLow')::float,
        (p_data->>'PriceOpen')::float,
        (p_data->>'PriceClose')::float,
        (p_data->>'PriceAverage')::float,
        (p_data->>'TotalVolume')::float,
        (p_data->>'Volume')::float,
        (p_data->>'TotalValue')::float,
        (p_data->>'PriceBid1')::float,
        (p_data->>'QuantityBid1')::float,
        (p_data->>'PriceBid2')::float,
        (p_data->>'QuantityBid2')::float,
        (p_data->>'PriceBid3')::float,
        (p_data->>'QuantityBid3')::float,
        (p_data->>'PriceAsk1')::float,
        (p_data->>'QuantityAsk1')::float,
        (p_data->>'PriceAsk2')::float,
        (p_data->>'QuantityAsk2')::float,
        (p_data->>'PriceAsk3')::float,
        (p_data->>'QuantityAsk3')::float,
        (p_data->>'BuyForeignValue')::float,
        (p_data->>'SellForeignValue')::float,
        (p_data->>'BuyForeignQuantity')::float,
        (p_data->>'CurrentForeignRoom')::float,
        (p_data->>'TotalActiveBuyVolume')::float,
        (p_data->>'TotalActiveSellVolume')::float,
        (p_data->>'PricePercentChange')::float,
        (p_data->>'PriceChange')::float
    )
    ON CONFLICT (symbol_ticker, date) DO UPDATE
    SET
        datetime = EXCLUDED.datetime,
        price_current = EXCLUDED.price_current,
        price_last = EXCLUDED.price_last,
        price_high = EXCLUDED.price_high,
        price_low = EXCLUDED.price_low,
        price_open = EXCLUDED.price_open,
        price_close = EXCLUDED.price_close,
        price_average = EXCLUDED.price_average,
        total_volume = EXCLUDED.total_volume,
        volume = EXCLUDED.volume,
        total_value = EXCLUDED.total_value,
        price_bid1 = EXCLUDED.price_bid1,
        quantity_bid1 = EXCLUDED.quantity_bid1,
        price_bid2 = EXCLUDED.price_bid2,
        quantity_bid2 = EXCLUDED.quantity_bid2,
        price_bid3 = EXCLUDED.price_bid3,
        quantity_bid3 = EXCLUDED.quantity_bid3,
        price_ask1 = EXCLUDED.price_ask1,
        quantity_ask1 = EXCLUDED.quantity_ask1,
        price_ask2 = EXCLUDED.price_ask2,
        quantity_ask2 = EXCLUDED.quantity_ask2,
        price_ask3 = EXCLUDED.price_ask3,
        quantity_ask3 = EXCLUDED.quantity_ask3,
        buy_foreign_value = EXCLUDED.buy_foreign_value,
        sell_foreign_value = EXCLUDED.sell_foreign_value,
        buy_foreign_quantity = EXCLUDED.buy_foreign_quantity,
        current_foreign_room = EXCLUDED.current_foreign_room,
        total_active_buy_volume = EXCLUDED.total_active_buy_volume,
        total_active_sell_volume = EXCLUDED.total_active_sell_volume,
        price_percent_change = EXCLUDED.price_percent_change,
        price_change = EXCLUDED.price_change;
END;
$$ LANGUAGE plpgsql;