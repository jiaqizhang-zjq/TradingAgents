"""Financial situation memory using BM25 for lexical similarity matching.

Uses BM25 (Best Matching 25) algorithm for retrieval - no API calls,
no token limits, works offline with any LLM provider.
"""

from rank_bm25 import BM25Okapi
from typing import List, Tuple, Optional, Dict, Any
import re

from tradingagents.constants import DEFAULT_DB_PATH
from tradingagents.agents.utils.memory_storage import (
    init_database,
    save_records,
    load_records,
    save_backtest_record,
    clear_records,
)
from tradingagents.agents.utils.memory_learner import learn_from_research_records
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


class FinancialSituationMemory:
    """Memory system for storing and retrieving financial situations using BM25."""

    def __init__(self, name: str, config: dict = None):
        """Initialize the memory system.

        Args:
            name: Name identifier for this memory instance
            config: Configuration dict (kept for API compatibility, not used for BM25)
        """
        self.name = name
        self.documents: List[str] = []
        self.recommendations: List[str] = []
        self.returns: List[float] = []
        self.bm25 = None
        self.db_path = DEFAULT_DB_PATH
        
        if config:
            self.db_path = config.get("db_path", self.db_path)
        
        init_database(self.db_path)
        self.load_from_db()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25 indexing.

        Simple whitespace + punctuation tokenization with lowercasing.
        """
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

    def _rebuild_index(self):
        """Rebuild the BM25 index after adding documents."""
        if self.documents:
            tokenized_docs = [self._tokenize(doc) for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_docs)
        else:
            self.bm25 = None

    def add_situations(self, situations_and_advice: List[Tuple[str, str, float]]):
        """Add financial situations and their corresponding advice with returns.

        Args:
            situations_and_advice: List of tuples (situation, recommendation, return)
        """
        for situation, recommendation, return_value in situations_and_advice:
            self.documents.append(situation)
            self.recommendations.append(recommendation)
            self.returns.append(return_value)

        self._rebuild_index()
        self.save_to_db()

    def get_memories(self, current_situation: str, n_matches: int = 1) -> List[dict]:
        """Find matching recommendations using BM25 similarity.

        Args:
            current_situation: The current financial situation to match against
            n_matches: Number of top matches to return

        Returns:
            List of dicts with matched_situation, recommendation, similarity_score, and actual_return
        """
        if not self.documents or self.bm25 is None:
            return []

        query_tokens = self._tokenize(current_situation)
        scores = self.bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_matches]

        results = []
        max_score = max(scores) if max(scores) > 0 else 1

        for idx in top_indices:
            normalized_score = scores[idx] / max_score if max_score > 0 else 0
            results.append({
                "matched_situation": self.documents[idx],
                "recommendation": self.recommendations[idx],
                "similarity_score": normalized_score,
                "actual_return": self.returns[idx] if idx < len(self.returns) else None,
            })

        return results

    # --- Storage delegation ---

    def save_to_db(self):
        """Save current memory data to database."""
        save_records(self.db_path, self.name, self.documents, self.recommendations, self.returns)

    def load_from_db(self):
        """Load memory data from database."""
        self.documents, self.recommendations, self.returns = load_records(self.db_path, self.name)
        self._rebuild_index()

    def update_from_backtest(self, symbol: str, trade_date: str, situation: str, 
                           recommendation: str, actual_return: float):
        """Update memory from backtest results.

        Args:
            symbol: Stock symbol
            trade_date: Trade date
            situation: Financial situation description
            recommendation: Action taken
            actual_return: Actual return achieved
        """
        self.documents.append(situation)
        self.recommendations.append(recommendation)
        self.returns.append(actual_return)
        self._rebuild_index()
        save_backtest_record(self.db_path, self.name, symbol, trade_date, 
                           situation, recommendation, actual_return)

    def clear(self):
        """Clear all stored memories."""
        self.documents = []
        self.recommendations = []
        self.returns = []
        self.bm25 = None
        clear_records(self.db_path, self.name)

    # --- Learning delegation ---

    def learn_from_research_records(self, limit: int = 100):
        """Learn from verified research records in database, combining with analysis reports.
        
        Args:
            limit: Maximum number of records to learn from
        """
        new_docs, new_recs, new_rets, count = learn_from_research_records(
            db_path=self.db_path,
            memory_name=self.name,
            existing_documents=self.documents,
            limit=limit,
        )
        
        if count > 0:
            self.documents.extend(new_docs)
            self.recommendations.extend(new_recs)
            self.returns.extend(new_rets)
            self._rebuild_index()
            self.save_to_db()
            logger.info("✅ Memory %s 从研究记录学习了 %d 条新记录", self.name, count)
        else:
            logger.info("⏭️  Memory %s 没有新的研究记录需要学习", self.name)


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory("test_memory")

    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    matcher.add_situations(example_data)

    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            logger.info("Match %d:", i)
            logger.info("  Similarity Score: %.2f", rec['similarity_score'])
            logger.info("  Matched Situation: %s", rec['matched_situation'])
            logger.info("  Recommendation: %s", rec['recommendation'])

    except Exception as e:
        logger.error("Error during recommendation: %s", e)
