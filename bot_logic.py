import pandas as pd
import copy
import redis_client
import json
from rbc_parser import parse_quotes
import os
from dotenv import load_dotenv
from io import StringIO
import logging
from models import CurrencyStatistics, QuotesData, CurrencyCode, CityCode
from typing import Union


logger = logging.getLogger(__name__)

base_url = 'https://cash.rbc.ru/cash/?currency={currency_code}&city={city_code}&deal={operation_code}&amount=1'
div_container = "quote__office__content js-office-content"

# Load .env variables
load_dotenv()

TTL_QUOTES_IN_REDIS = int(os.getenv("TTL_QUOTES_IN_REDIS", 600))
TTL_STATS_IN_REDIS = int(os.getenv("TTL_STATS_IN_REDIS", 600))


def _get_data_frame(data: QuotesData) -> pd.DataFrame:
    return pd.DataFrame({
        'bank': data.banks_names,
        'quote': data.quotes,
        'time': data.times,
        'commissions': data.commissions,
        'currency': data.currency,
    })


def _merge_df(df_buy: pd.DataFrame, df_sell: pd.DataFrame) -> pd.DataFrame:

    df_buy = df_buy.rename(columns={"quote": "buy_quote"})
    df_sell = df_sell.rename(columns={"quote": "sell_quote"})

    # Merge on 'bank' (base is buy df)
    merged = pd.merge(df_buy, df_sell[["bank", "sell_quote"]], on="bank", how="left")

    # Calculate spread
    merged["spread"] = round(merged["buy_quote"] - merged["sell_quote"], 2) 
    merged["spread_percent"] = round((merged["spread"] / merged["sell_quote"]) * 100, 2) 
    merged["avg_price"] = round((merged["buy_quote"] + merged["sell_quote"]) / 2, 2) 

    # Sort merged df
    merged = merged.sort_values(by='buy_quote')

    return merged[["currency", "bank", "buy_quote", "sell_quote", "spread",
                  "spread_percent", "avg_price",  "time", "commissions"]]


def get_quotes_df_from_redis_cache(redis_json_name: str) -> pd.DataFrame | None:
    try:
        data = redis_client.REDIS_CLIENT.get(redis_json_name)
        if data is not None:
            df_merged = pd.read_json(StringIO(data))
            df_merged['time'] = pd.to_datetime(df_merged['time']).dt.tz_localize('Europe/Moscow')
            return df_merged
        else:
            return None
    except Exception as e:
        logger.error("Couldn`t retrive quotes from Redis: %s", e)
        return None


def get_statistics_df_from_redis_cache(redis_json_name: str) -> pd.DataFrame | None:
    data = redis_client.REDIS_CLIENT.get(redis_json_name)
    if data is not None:
        prepared_response = json.loads(data)
        return prepared_response
    else:
        return None


def set_quotes_to_redis_cache(redis_json_name: str, df_merged: pd.DataFrame) -> None:
    try:
        redis_client.REDIS_CLIENT.set(redis_json_name,
                                      df_merged.to_json(orient='records'), 
                                      ex=TTL_QUOTES_IN_REDIS
                                      )
    except Exception as e:
        logger.error("Data where not save in Redis: %s", e)


def set_statistics_to_redis_cache(redis_json_name, df_merged):
    try:
        redis_client.REDIS_CLIENT.setex(redis_json_name,
                                        TTL_STATS_IN_REDIS,
                                        json.dumps(df_merged)
                                        )
    except Exception as e:
        logger.error("Data where not saved in Redis: %s", e)


def get_currency_code(currency: Union[str, CurrencyCode]) -> int:
    if isinstance(currency, str):
        return CurrencyCode[currency.upper()].value
    return currency.value


def get_city_code(city: Union[str, CityCode]) -> int:
    if isinstance(city, str):
        return CityCode[city.upper()].value
    return city.value


def get_quotes_df(currency: str,
                  city: str = 'Moscow',
                  num_of_returned_banks: int = 5,
                  return_all_banks: bool = False
                  ) -> pd.DataFrame:

    redis_json_name = f'{city.lower()}:{currency.lower()}'
    cached_quotes = None

    if redis_client.REDIS_AVAILABLE:
        try:
            cached_quotes = get_quotes_df_from_redis_cache(redis_json_name)
        except Exception as e:
            cached_quotes = None
            logger.error("Couldn`t retrive quotes from Redis: %s", e)

    if cached_quotes is not None:
        return cached_quotes if return_all_banks else cached_quotes.head(num_of_returned_banks)

    currency_code = get_currency_code(currency)
    city_code = get_city_code(city)

    df_buy = None
    df_sell = None
    df_merged = None

    buy_url = base_url.format(currency_code=currency_code,
                              city_code=city_code,
                              operation_code='buy')

    sell_url = base_url.format(currency_code=currency_code,
                               city_code=city_code,
                               operation_code='sell')

    df_buy = _get_data_frame(parse_quotes(buy_url, div_container, currency))
    df_sell = _get_data_frame(parse_quotes(sell_url, div_container, currency))

    df_merged = _merge_df(df_buy, df_sell)

    if redis_client.REDIS_CLIENT is not None:
        try:
            set_quotes_to_redis_cache(redis_json_name, df_merged)
        except Exception as e:
            logger.error("Couldn`t save quotes from Redis: %s", e)

    return df_merged if return_all_banks else df_merged.head(num_of_returned_banks)


def _get_several_currencies_in_city(city: str, 
                                    currencies_list: list[str]
                                    ) -> pd.DataFrame:
    merged_df = pd.DataFrame()
    for currency in currencies_list:
        df = get_quotes_df(currency, city, return_all_banks=True)
        if df is not None and not df.empty:  # ✅ if the result is valid
            merged_df = pd.concat([merged_df, df], ignore_index=True)
    return merged_df


def _calculate_statistics(df: pd.DataFrame) -> dict[str, CurrencyStatistics]:

    available_currencies = set(df['currency'])

    statistics_template: CurrencyStatistics = {
        'num_of_available_buys': 0,
        'num_of_available_sells': 0,
        'avg_buys': None,
        'avg_sells': None,
        'avg_price': None,
        'min_spread_rub': 0.0,
        'max_spread_rub': 0.0,
        'avg_spread_rub': None,
    }

    stat: dict[str, CurrencyStatistics] = {}

    for currency in available_currencies:
        stat[currency] = copy.deepcopy(statistics_template)
        r = stat[currency]

        df_cur = df[df["currency"] == currency]

        r['num_of_available_buys'] = int(df_cur['buy_quote'].notna().sum())
        r['num_of_available_sells'] = int(df_cur['sell_quote'].notna().sum())

        avg_buys = df_cur['buy_quote'].mean()
        r['avg_buys'] = round(avg_buys, 2) if pd.notna(avg_buys) else None

        avg_sells = df_cur['sell_quote'].mean()
        r['avg_sells'] = round(avg_sells, 2) if pd.notna(avg_sells) else None

        avg_price = df_cur['avg_price'].mean()
        r['avg_price'] = round(avg_price, 2) if pd.notna(avg_price) else None

        r['min_spread_rub'] = float(round(df_cur['spread'].min(), 2))
        r['max_spread_rub'] = float(round(df_cur['spread'].max(), 2))
        avg_spread = df_cur['spread'].mean()
        r['avg_spread_rub'] = round(avg_spread, 2) if pd.notna(avg_spread) else None

    return stat


def get_statistics(city: str,
                   currencies_list: list[str]
                   ) -> dict[str, CurrencyStatistics]:
    redis_json_name = f"statistics:{city.lower()}"
    # First we check redis storage. If empty we parsing from website.
    if redis_client.REDIS_AVAILABLE is not None:
        try:
            response = get_statistics_df_from_redis_cache(redis_json_name)
            if response is not None:
                return json.loads(response)
        except Exception as e:
            logger.error('Couldn`t get statistics from Redis: %s', e)

    # If no data in cache then we parse website
    df = _get_several_currencies_in_city(city, currencies_list)

    if df.empty:
        return {}

    # calculating statistics and pack result in dict
    response = _calculate_statistics(df)

    if redis_client.REDIS_CLIENT is not None:
        # save parsed data to redis for TTL minutes set in .env
        set_statistics_to_redis_cache(redis_json_name,
                                      json.dumps(response)
                                      )

    return response
