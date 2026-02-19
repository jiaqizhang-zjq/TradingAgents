from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
from tradingagents.agents.utils.agent_utils import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement
from tradingagents.dataflows.config import get_config


def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        fundamentals_data = ""
        try:
            fundamentals_data = get_fundamentals.invoke({"ticker": ticker, "curr_date": current_date})
        except Exception as e:
            fundamentals_data = f"Error fetching fundamentals: {str(e)}"
        
        balance_sheet_data = ""
        try:
            balance_sheet_data = get_balance_sheet.invoke({"ticker": ticker, "freq": "quarterly", "curr_date": current_date})
        except Exception as e:
            balance_sheet_data = f"Error fetching balance sheet: {str(e)}"
        
        cashflow_data = ""
        try:
            cashflow_data = get_cashflow.invoke({"ticker": ticker, "freq": "quarterly", "curr_date": current_date})
        except Exception as e:
            cashflow_data = f"Error fetching cashflow: {str(e)}"
        
        income_statement_data = ""
        try:
            income_statement_data = get_income_statement.invoke({"ticker": ticker, "freq": "quarterly", "curr_date": current_date})
        except Exception as e:
            income_statement_data = f"Error fetching income statement: {str(e)}"
        
        system_message = (
            """You are a researcher tasked with analyzing fundamental information about a company. Based on the provided fundamental data, balance sheet, cashflow statement, and income statement, please write a comprehensive report of the company's fundamental information such as financial documents, company profile, basic company financials, and company financial history to gain a full view of the company's fundamental information to inform traders. Make sure to include as much detail as possible. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions. Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    "{system_message}"
                    "\nFor your reference, the current date is {current_date}. The company we want to look at is {ticker}."
                    "\n\nFundamentals Data:\n{fundamentals_data}"
                    "\n\nBalance Sheet:\n{balance_sheet_data}"
                    "\n\nCashflow Statement:\n{cashflow_data}"
                    "\n\nIncome Statement:\n{income_statement_data}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(fundamentals_data=fundamentals_data)
        prompt = prompt.partial(balance_sheet_data=balance_sheet_data)
        prompt = prompt.partial(cashflow_data=cashflow_data)
        prompt = prompt.partial(income_statement_data=income_statement_data)

        chain = prompt | llm

        result = chain.invoke(state["messages"])
        report = result.content

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
