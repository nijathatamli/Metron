"""
Metron Coin lifecycle — earn and spend operations.

1 Metron Coin = 1 AZN.  Coins are fractional (two-decimal precision).
All monetary arithmetic uses Python's built-in float rounded to 2 dp;
for production billing a Decimal type is recommended.
"""

from __future__ import annotations

from typing import TypedDict


class SpendResult(TypedDict):
    """Return type of :func:`spend_coins`."""
    coins_deducted: float
    cash_paid: float
    remaining_balance: float


def earn_coins(trip_fare_azn: float, cashback_percent: int) -> float:
    """
    Calculate Metron Coins earned for a single metro trip.

    Args:
        trip_fare_azn: The fare paid for the trip (AZN).
        cashback_percent: Cashback rate determined by density (0–15).

    Returns:
        The number of coins earned (1 coin = 1 AZN).

    Raises:
        ValueError: If inputs are negative or cashback_percent > 100.
    """
    if trip_fare_azn < 0:
        raise ValueError("trip_fare_azn must be ≥ 0")
    if not 0 <= cashback_percent <= 100:
        raise ValueError("cashback_percent must be 0–100")

    coins = trip_fare_azn * (cashback_percent / 100)
    return round(coins, 2)


def spend_coins(product_price_azn: float, user_coin_balance: float) -> SpendResult:
    """
    Determine how many coins to deduct and how much cash the user still owes.

    Rules:
      - If the user has enough coins to cover the full price, deduct only
        the product price and charge zero cash.
      - If the user has fewer coins than the price, deduct all coins and
        charge the remainder in cash (partial spend).
      - Zero-coin products: deduct nothing, charge full price in cash.
      - If user_coin_balance is zero, the full price is charged in cash.

    Args:
        product_price_azn: Total product price in AZN.
        user_coin_balance: User's current coin balance.

    Returns:
        SpendResult with coins_deducted, cash_paid, remaining_balance.

    Raises:
        ValueError: If product_price_azn < 0 or user_coin_balance < 0.
    """
    if product_price_azn < 0:
        raise ValueError("product_price_azn must be ≥ 0")
    if user_coin_balance < 0:
        raise ValueError("user_coin_balance must be ≥ 0")

    # Edge case: free product
    if product_price_azn == 0:
        return SpendResult(
            coins_deducted=0.0,
            cash_paid=0.0,
            remaining_balance=round(user_coin_balance, 2),
        )

    coins_to_use = min(user_coin_balance, product_price_azn)
    cash_owed = product_price_azn - coins_to_use

    return SpendResult(
        coins_deducted=round(coins_to_use, 2),
        cash_paid=round(cash_owed, 2),
        remaining_balance=round(user_coin_balance - coins_to_use, 2),
    )
