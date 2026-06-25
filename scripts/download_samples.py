"""
Generate sample financial PDFs for testing the RAG pipeline.

Produces two realistic financial summary PDFs in the data/ folder:
1. Apple Q3 2024 quarterly financial summary
2. NVIDIA 2024 annual financial highlights
"""

import os
from fpdf import FPDF


class FinancialPDF(FPDF):
    """Custom PDF class with header/footer for financial documents."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, self.title, align="C")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, title)
        self.ln(8)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def financial_table(self, headers: list, rows: list, col_widths: list = None):
        """Render a simple financial data table."""
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        # Header row
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(30, 30, 30)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, border=1, fill=True, align="C")
        self.ln()

        # Data rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        for row in rows:
            for i, cell in enumerate(row):
                align = "L" if i == 0 else "R"
                self.cell(col_widths[i], 7, str(cell), border=1, align=align)
            self.ln()
        self.ln(4)


def generate_apple_q3_2024(output_path: str):
    """Generate a realistic Apple Q3 2024 quarterly financial summary PDF."""
    pdf = FinancialPDF()
    pdf.alias_nb_pages()
    pdf.title = "Apple Inc. -- Q3 2024 Consolidated Financial Statements"
    pdf.add_page()

    pdf.section_title("Quarterly Financial Summary (Unaudited)")
    pdf.body_text(
        "The following condensed consolidated financial statements present Apple Inc.'s "
        "results for the third fiscal quarter ended June 29, 2024. All figures are in "
        "millions of USD unless otherwise noted."
    )

    pdf.section_title("Consolidated Statement of Operations")

    pdf.financial_table(
        headers=["Metric", "Q3 2024", "Q3 2023", "Change (%)"],
        rows=[
            ["Total Net Sales", "$85,777", "$81,797", "+4.9%"],
            ["Cost of Sales", "$46,099", "$45,384", "+1.6%"],
            ["Gross Margin", "$39,678", "$36,413", "+9.0%"],
            ["Gross Margin (%)", "46.3%", "44.5%", "+1.8pp"],
            ["Operating Expenses", "$14,327", "$13,415", "+6.8%"],
            ["  Research & Development", "$8,008", "$7,442", "+7.6%"],
            ["  Selling, General & Admin", "$6,319", "$5,973", "+5.8%"],
            ["Operating Income", "$25,351", "$22,998", "+10.2%"],
            ["Net Income", "$21,448", "$19,881", "+7.9%"],
            ["Earnings Per Share (Diluted)", "$1.40", "$1.26", "+11.1%"],
        ],
        col_widths=[85, 35, 35, 35],
    )

    pdf.section_title("Revenue by Product Category")
    pdf.financial_table(
        headers=["Category", "Q3 2024 Revenue", "Q3 2023 Revenue", "Change (%)"],
        rows=[
            ["iPhone", "$39,296", "$39,669", "-0.9%"],
            ["Services", "$24,213", "$21,213", "+14.1%"],
            ["Mac", "$7,009", "$6,840", "+2.5%"],
            ["iPad", "$7,162", "$5,791", "+23.7%"],
            ["Wearables, Home & Accessories", "$8,097", "$8,284", "-2.3%"],
        ],
        col_widths=[70, 40, 40, 40],
    )

    pdf.section_title("Revenue by Geographic Region")
    pdf.financial_table(
        headers=["Region", "Q3 2024 Revenue", "Q3 2023 Revenue"],
        rows=[
            ["Americas", "$37,665", "$35,383"],
            ["Europe", "$21,884", "$20,207"],
            ["Greater China", "$14,724", "$15,758"],
            ["Japan", "$5,097", "$4,821"],
            ["Rest of Asia Pacific", "$6,407", "$5,628"],
        ],
        col_widths=[70, 60, 60],
    )

    pdf.section_title("Management Discussion & Analysis Highlights")
    pdf.body_text(
        "Apple posted June quarter revenue of $85.8 billion, up 5 percent year-over-year, "
        "driven by an all-time revenue record in Services of $24.2 billion and strong iPad "
        "growth of 24 percent. iPhone revenue was essentially flat at $39.3 billion, while "
        "Mac revenue grew 2.5 percent to $7.0 billion. Wearables, Home and Accessories "
        "declined 2.3 percent to $8.1 billion."
    )
    pdf.body_text(
        "The Company generated approximately $29 billion in operating cash flow during the "
        "quarter and returned over $29 billion to shareholders through share repurchases "
        "and dividends. Apple's installed base of active devices reached new all-time highs "
        "across all product categories and geographic segments."
    )
    pdf.body_text(
        "Gross margin expanded 180 basis points year-over-year to 46.3 percent, driven by "
        "favorable mix shift toward Services and commodity cost improvements. Net income "
        "totaled $21.4 billion, with diluted earnings per share of $1.40, up 11 percent "
        "compared to the year-ago quarter."
    )
    pdf.body_text(
        "Looking ahead, the Company expects the September quarter revenue to grow year-over-year "
        "at a rate similar to the June quarter, despite foreign exchange headwinds. The Services "
        "segment is expected to grow double-digits, while gross margin is projected between "
        "45.5 percent and 46.5 percent."
    )

    pdf.output(output_path)
    print(f"  Generated: {output_path}")


def generate_nvidia_2024_annual(output_path: str):
    """Generate a realistic NVIDIA 2024 annual financial highlights PDF."""
    pdf = FinancialPDF()
    pdf.alias_nb_pages()
    pdf.title = "NVIDIA Corporation -- Fiscal Year 2024 Annual Financial Highlights"
    pdf.add_page()

    pdf.section_title("Annual Financial Overview")
    pdf.body_text(
        "The following highlights present NVIDIA Corporation's financial results for the "
        "fiscal year ended January 28, 2024. All figures are in millions of USD unless "
        "otherwise noted. NVIDIA delivered record revenue driven by surging demand for "
        "data center accelerated computing and AI platforms."
    )

    pdf.section_title("Annual Income Statement Highlights")
    pdf.financial_table(
        headers=["Metric", "FY 2024", "FY 2023", "Change (%)"],
        rows=[
            ["Total Revenue", "$60,922", "$26,974", "+125.9%"],
            ["Cost of Revenue", "$16,723", "$11,618", "+43.9%"],
            ["Gross Profit", "$44,199", "$15,356", "+187.8%"],
            ["Gross Margin (%)", "72.6%", "56.9%", "+15.7pp"],
            ["Operating Expenses", "$11,227", "$11,132", "+0.9%"],
            ["  Research & Development", "$8,675", "$7,339", "+18.2%"],
            ["  Selling, General & Admin", "$2,552", "$2,440", "+4.6%"],
            ["Operating Income", "$32,972", "$4,224", "+680.6%"],
            ["Net Income", "$29,760", "$4,368", "+581.3%"],
            ["Earnings Per Share (Diluted)", "$11.93", "$1.74", "+585.6%"],
        ],
        col_widths=[85, 35, 35, 35],
    )

    pdf.section_title("Revenue by Market Platform")
    pdf.financial_table(
        headers=["Platform", "FY 2024 Revenue", "FY 2023 Revenue", "Change (%)"],
        rows=[
            ["Data Center", "$47,525", "$15,005", "+216.7%"],
            ["Gaming", "$10,447", "$9,067", "+15.2%"],
            ["Professional Visualization", "$1,553", "$1,544", "+0.6%"],
            ["Automotive", "$1,091", "$903", "+20.8%"],
            ["OEM & Other", "$306", "$455", "-32.7%"],
        ],
        col_widths=[70, 40, 40, 40],
    )

    pdf.section_title("Annual Balance Sheet Highlights")
    pdf.financial_table(
        headers=["Metric", "FY 2024", "FY 2023"],
        rows=[
            ["Cash & Marketable Securities", "$25,984", "$13,296"],
            ["Total Assets", "$65,728", "$44,187"],
            ["Total Liabilities", "$22,750", "$19,081"],
            ["Shareholders' Equity", "$42,978", "$25,106"],
        ],
        col_widths=[85, 52, 52],
    )

    pdf.section_title("Management Discussion & Analysis")
    pdf.body_text(
        "NVIDIA achieved record revenue of $60.9 billion in fiscal 2024, more than doubling "
        "the prior year. Data Center revenue led the growth, surging 217 percent to $47.5 "
        "billion, driven by unprecedented demand for the NVIDIA Hopper GPU architecture and "
        "accelerated computing platforms used in generative AI, large language model training, "
        "and inference workloads across cloud service providers, enterprises, and sovereign AI "
        "initiatives."
    )
    pdf.body_text(
        "Gross margin expanded dramatically to 72.6 percent from 56.9 percent, reflecting "
        "the higher value-add of Data Center products and improved supply chain execution. "
        "Operating income reached $33.0 billion, an increase of nearly 7x year-over-year, "
        "demonstrating the strong operating leverage in NVIDIA's business model."
    )
    pdf.body_text(
        "Gaming revenue of $10.4 billion grew 15 percent, driven by the GeForce RTX 40 Series "
        "GPUs and increasing demand for AI-powered gaming experiences. The Company ended the "
        "year with $26.0 billion in cash and marketable securities, providing substantial "
        "flexibility for investments in R&D and strategic opportunities."
    )
    pdf.body_text(
        "NVIDIA returned approximately $7.2 billion to shareholders through a combination of "
        "share repurchases ($6.0 billion) and cash dividends ($1.2 billion) during fiscal 2024. "
        "Looking ahead, the Company expects continued strong demand for its next-generation "
        "Blackwell architecture and accelerated computing platforms as enterprises across all "
        "industries adopt AI to transform their operations."
    )

    pdf.output(output_path)
    print(f"  Generated: {output_path}")


def main():
    """Generate sample financial PDFs in the data/ directory."""
    # Determine the data directory (relative to project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    print("Generating sample financial PDFs...")
    generate_apple_q3_2024(os.path.join(data_dir, "apple_q3_2024_summary.pdf"))
    generate_nvidia_2024_annual(os.path.join(data_dir, "nvidia_2024_annual_summary.pdf"))
    print("Done! Sample PDFs are ready in the data/ folder.")


if __name__ == "__main__":
    main()
