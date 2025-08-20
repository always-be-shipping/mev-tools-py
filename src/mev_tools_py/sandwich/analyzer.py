from typing import List, Dict
from decimal import Decimal
from collections import defaultdict, Counter

from mev_tools_py.sandwich.models import SandwichAttack, SandwichStatistics


class SandwichAnalyzer:
    """Analyzer for sandwich attack patterns and statistics."""

    def __init__(self):
        pass

    def analyze_attacks(self, attacks: List[SandwichAttack]) -> SandwichStatistics:
        """Generate comprehensive statistics from a list of sandwich attacks."""
        if not attacks:
            return self._empty_statistics()

        # Basic counts and totals
        total_attacks = len(attacks)
        total_profit = sum(attack.profit_amount for attack in attacks)
        total_victim_loss = sum(attack.victim_loss_amount for attack in attacks)

        # Find block range
        block_numbers = [attack.block_number for attack in attacks]
        from_block = min(block_numbers)
        to_block = max(block_numbers)

        # Calculate averages
        average_profit = (
            total_profit / total_attacks if total_attacks > 0 else Decimal("0")
        )

        # Find most profitable attack
        most_profitable = (
            max(attacks, key=lambda x: x.profit_amount) if attacks else None
        )

        # Top attackers by profit
        attacker_profits = defaultdict(Decimal)
        for attack in attacks:
            attacker_profits[attack.attacker_address] += attack.profit_amount

        top_attackers = sorted(
            attacker_profits.items(), key=lambda x: x[1], reverse=True
        )[:10]  # Top 10

        # Most targeted pools
        pool_counts = Counter(attack.pool_address for attack in attacks)
        most_targeted_pools = pool_counts.most_common(10)

        return SandwichStatistics(
            from_block=from_block,
            to_block=to_block,
            total_attacks=total_attacks,
            total_profit=total_profit,
            total_victim_loss=total_victim_loss,
            average_profit_per_attack=average_profit,
            most_profitable_attack=most_profitable,
            top_attackers=top_attackers,
            most_targeted_pools=most_targeted_pools,
        )

    def analyze_attack_patterns(self, attacks: List[SandwichAttack]) -> Dict[str, any]:
        """Analyze patterns in sandwich attacks."""
        if not attacks:
            return {}

        # Attack type distribution
        type_distribution = Counter(attack.sandwich_type for attack in attacks)

        # Temporal patterns
        block_distribution = Counter(attack.block_number for attack in attacks)
        attacks_per_block = list(block_distribution.values())

        # Profit distribution
        profits = [float(attack.profit_amount) for attack in attacks]

        # Gas usage patterns
        gas_costs = [
            float(attack.gas_cost) for attack in attacks if attack.gas_cost > 0
        ]

        # Token pair analysis
        token_pairs = Counter(
            f"{pair[0][:8]}.../{pair[1][:8]}..."
            for attack in attacks
            for pair in [attack.token_pair]
        )

        # Victim count patterns
        victim_counts = Counter(len(attack.victim_txs) for attack in attacks)

        return {
            "attack_types": dict(type_distribution),
            "temporal_patterns": {
                "unique_blocks": len(block_distribution),
                "max_attacks_per_block": (
                    max(attacks_per_block) if attacks_per_block else 0
                ),
                "avg_attacks_per_block": (
                    sum(attacks_per_block) / len(attacks_per_block)
                    if attacks_per_block
                    else 0
                ),
            },
            "profit_analysis": {
                "min_profit": min(profits) if profits else 0,
                "max_profit": max(profits) if profits else 0,
                "avg_profit": sum(profits) / len(profits) if profits else 0,
                "median_profit": sorted(profits)[len(profits) // 2] if profits else 0,
            },
            "gas_analysis": {
                "avg_gas_cost": sum(gas_costs) / len(gas_costs) if gas_costs else 0,
                "total_gas_spent": sum(gas_costs),
            },
            "token_pairs": dict(token_pairs.most_common(10)),
            "victim_patterns": dict(victim_counts),
        }

    def calculate_attack_efficiency(self, attack: SandwichAttack) -> Dict[str, Decimal]:
        """Calculate efficiency metrics for a single attack."""
        efficiency_metrics = {}

        # Profit per gas ratio
        if attack.gas_cost > 0:
            efficiency_metrics["profit_per_gas"] = (
                attack.profit_amount / attack.gas_cost
            )
        else:
            efficiency_metrics["profit_per_gas"] = Decimal("0")

        # Profit per victim
        if attack.victim_txs:
            efficiency_metrics["profit_per_victim"] = attack.profit_amount / len(
                attack.victim_txs
            )
        else:
            efficiency_metrics["profit_per_victim"] = Decimal("0")

        # Price manipulation efficiency
        if attack.price_manipulation_pct > 0:
            efficiency_metrics["profit_per_price_impact"] = (
                attack.profit_amount / attack.price_manipulation_pct
            )
        else:
            efficiency_metrics["profit_per_price_impact"] = Decimal("0")

        # Volume efficiency
        if attack.total_volume_manipulated > 0:
            efficiency_metrics["profit_per_volume"] = (
                attack.profit_amount / attack.total_volume_manipulated
            )
        else:
            efficiency_metrics["profit_per_volume"] = Decimal("0")

        return efficiency_metrics

    def identify_sophisticated_attackers(
        self,
        attacks: List[SandwichAttack],
        min_attacks: int = 5,
        min_total_profit: Decimal = Decimal("1.0"),
    ) -> List[Dict[str, any]]:
        """Identify sophisticated/professional sandwich attackers."""
        attacker_stats = defaultdict(
            lambda: {
                "attacks": [],
                "total_profit": Decimal("0"),
                "total_gas": Decimal("0"),
                "victim_count": 0,
                "pools_targeted": set(),
                "attack_types": Counter(),
            }
        )

        # Aggregate stats per attacker
        for attack in attacks:
            addr = attack.attacker_address.lower()
            stats = attacker_stats[addr]

            stats["attacks"].append(attack)
            stats["total_profit"] += attack.profit_amount
            stats["total_gas"] += attack.gas_cost
            stats["victim_count"] += len(attack.victim_txs)
            stats["pools_targeted"].add(attack.pool_address)
            stats["attack_types"][attack.sandwich_type] += 1

        # Filter and analyze sophisticated attackers
        sophisticated = []
        for address, stats in attacker_stats.items():
            if (
                len(stats["attacks"]) >= min_attacks
                and stats["total_profit"] >= min_total_profit
            ):
                # Calculate sophistication metrics
                avg_profit = stats["total_profit"] / len(stats["attacks"])
                pools_diversity = len(stats["pools_targeted"])

                # Efficiency metrics
                avg_efficiency = sum(
                    self.calculate_attack_efficiency(attack)["profit_per_gas"]
                    for attack in stats["attacks"]
                ) / len(stats["attacks"])

                sophisticated.append(
                    {
                        "address": address,
                        "attack_count": len(stats["attacks"]),
                        "total_profit": stats["total_profit"],
                        "average_profit": avg_profit,
                        "pools_targeted": pools_diversity,
                        "total_victims": stats["victim_count"],
                        "attack_types": dict(stats["attack_types"]),
                        "average_efficiency": avg_efficiency,
                        "total_gas_spent": stats["total_gas"],
                    }
                )

        # Sort by total profit
        return sorted(sophisticated, key=lambda x: x["total_profit"], reverse=True)

    def detect_attack_clusters(
        self, attacks: List[SandwichAttack], block_window: int = 100
    ) -> List[Dict[str, any]]:
        """Detect clusters of sandwich attacks that might be coordinated."""
        if not attacks:
            return []

        # Sort attacks by block number
        sorted_attacks = sorted(attacks, key=lambda x: x.block_number)

        clusters = []
        current_cluster = [sorted_attacks[0]]

        for i in range(1, len(sorted_attacks)):
            attack = sorted_attacks[i]
            prev_attack = sorted_attacks[i - 1]

            # Check if attack belongs to current cluster
            if attack.block_number - prev_attack.block_number <= block_window:
                current_cluster.append(attack)
            else:
                # Finalize current cluster and start new one
                if len(current_cluster) > 1:
                    clusters.append(self._analyze_cluster(current_cluster))
                current_cluster = [attack]

        # Don't forget the last cluster
        if len(current_cluster) > 1:
            clusters.append(self._analyze_cluster(current_cluster))

        return clusters

    def _analyze_cluster(self, cluster_attacks: List[SandwichAttack]) -> Dict[str, any]:
        """Analyze a cluster of attacks."""
        # Basic cluster stats
        block_range = (
            min(attack.block_number for attack in cluster_attacks),
            max(attack.block_number for attack in cluster_attacks),
        )

        # Attacker analysis
        attackers = set(attack.attacker_address for attack in cluster_attacks)
        pools = set(attack.pool_address for attack in cluster_attacks)

        # Temporal density
        block_span = block_range[1] - block_range[0] + 1
        attack_density = len(cluster_attacks) / block_span

        # Profit analysis
        total_profit = sum(attack.profit_amount for attack in cluster_attacks)

        return {
            "attack_count": len(cluster_attacks),
            "block_range": block_range,
            "block_span": block_span,
            "unique_attackers": len(attackers),
            "unique_pools": len(pools),
            "attack_density": attack_density,
            "total_profit": total_profit,
            "attackers": list(attackers),
            "pools": list(pools),
        }

    def _empty_statistics(self) -> SandwichStatistics:
        """Return empty statistics object."""
        return SandwichStatistics(
            from_block=0,
            to_block=0,
            total_attacks=0,
            total_profit=Decimal("0"),
            total_victim_loss=Decimal("0"),
            average_profit_per_attack=Decimal("0"),
            most_profitable_attack=None,
            top_attackers=[],
            most_targeted_pools=[],
        )
