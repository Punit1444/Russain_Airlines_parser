import json
import re
import os
import PyPDF2
import csv
import pdfplumber
from datetime import datetime
from pprint import pprint

DATE_PATTERN = r".*?(\d{2}/\d{2}/\d{2})"
GST_PATTERN = r"\d{2}[A-Za-z]{5}\d{4}[A-Za-z]{1}\d{1}[Z]{1}[A-Za-z\d]{1}"
PNR_PATTERN = r"[A-Z0-9]{6}"
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"


def find_pattern(pattern, text, find_all=False):
    compiled_pattern = re.compile(pattern)
    if find_all:
        matches = compiled_pattern.findall(text)
    else:
        matches = compiled_pattern.search(text)
        if matches:
            matches = [matches.group(0)]
        else:
            matches = []
    return matches


def find_indian_states_and_ut(text):
    states_and_ut = [
        "ANDHRA PRADESH",
        "ARUNACHAL PRADESH",
        "ASSAM",
        "BIHAR",
        "CHHATTISGARH",
        "GOA",
        "GUJARAT",
        "HARYANA",
        "HIMACHAL PRADESH",
        "JHARKHAND",
        "KARNATAKA",
        "KERALA",
        "MADHYA PRADESH",
        "MAHARASHTRA",
        "MANIPUR",
        "MEGHALAYA",
        "MIZORAM",
        "NAGALAND",
        "ODISHA",
        "PUNJAB",
        "RAJASTHAN",
        "SIKKIM",
        "TAMIL NADU",
        "TELANGANA",
        "TRIPURA",
        "UTTAR PRADESH",
        "UTTARAKHAND",
        "WEST BENGAL",
        "ANDAMAN AND NICOBAR ISLANDS",
        "CHANDIGARH",
        "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
        "LAKSHADWEEP",
        "DELHI",
        "PUDUCHERRY",
    ]

    found_states_and_ut = []

    for state in states_and_ut:
        if re.search(state, text):
            found_states_and_ut.append(state)

    return found_states_and_ut


def find_top_details(page_text):
    invoice_no = page_text.split("Invoice No. ")[1].split(" ")[0]

    date_part = page_text.split("Dated ")[1].split("\n")[0]

    airlines = page_text.split('\n')
    for i, line in enumerate(airlines):
        if "Ref. No." in line and i + 1 < len(airlines):
            airline_name = airlines[i + 1]
            break
    else:
        output = "Output not found."


    addr = page_text.split('\n')
    address_type = addr[3]+addr[4]+addr[5]
    
    final_data = []

    top_details_strings = page_text.split("\n")
    doc_type = top_details_strings[10]
    airline_gst = find_pattern(GST_PATTERN, page_text, find_all=True)[0]
    party_name = page_text.split("Party :")[1].split("\n")[0].strip()
    amt_words = page_text.split("Amount Chargeable (in words) E. & O.E")[1].strip().split('\n')[0]
    tax_amt_words = page_text.split("Tax Amount (in words) : ")[1].split("\n")[0].strip()
    company_pan = page_text.split("Company's PAN :")[1].split("\n")[0].strip()  

    final_data.extend(
        [
            {"key": "Customer Name", "value": party_name},
            {"key": "Company Pan", "value": company_pan},
            {"key": "Tax Amount in words", "value": tax_amt_words},
            {"key": "Amount in words", "value": amt_words},
            {"key": "Party name", "value": party_name},
            {"key": "Airlines GST", "value": airline_gst},
            {"key": "Document Type", "value": doc_type},
            {"key": "Address", "value": address_type},
            {"key": "Dated ", "value": date_part},
            {"key": "Invoice No ", "value": invoice_no},
        ]
    )

    return final_data



def find_table_details(tables):


    HSN_SAC_Code = None
    Taxable_value = 0
    IGST_Rate = 0
    IGST_Amount = 0
    CGST_Amount = 0
    CGST_Amount = 0
    SGST_Rate = 0
    SGST_Amount = 0
    total_amount = 0
    Non_Taxable= 0


    #'Description': row['1'].replace('\n',' '),
    HSN_SAC_Code=tables[0][0][3]
    SL_NO=tables[0][0][0]
    Description=tables[0][0][2]
    Amount=tables[0][0][6]
    Travel_code=tables[0][1][2]
    Taxable_value=tables[1][0][1].split('\n')[2].strip()
    Taxable_amt=tables[1][0][6].split('\n')[2].strip()
    Total=tables[0][6][6]
    CGST_Amount=tables[0][3][6]
    CGST_Rate=tables[0][3][2].split(' ')[1].strip()
    SGST_Amount=tables[0][4][6]
    SGST_Rate=tables[0][4][2].split(' ')[1].strip()
    

    

    final_data = [
    {"key": "HSN", "value": HSN_SAC_Code},
    {"key": "SL_NO", "value": SL_NO},
    {"key": "Description", "value": Description},
    {"key": "Amount", "value": Amount},
    {"key": "Travel_code", "value": Travel_code},
    {"key": "Taxable_value", "value": Taxable_value},
    {"key": "Taxable_amt", "value": Taxable_amt},
    {"key": "Total", "value": Total},
    {"key": "CGST_Amount", "value": CGST_Amount},
    {"key": "CGST_Rate", "value": CGST_Rate},
    {"key": "SGST_Amount", "value": SGST_Amount},
    {"key": "SGST_Rate", "value": SGST_Rate},
    ]
    return final_data



# Open the PDF files in the given directory
pdf_dir = r"/Users/finkraft/Desktop/Parsers/test/"
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
all_data = []
for pdf_file in pdf_files:
    try:
        print("pdf_file", pdf_file)
        with pdfplumber.open(os.path.join(pdf_dir, pdf_file)) as pdf_file_buffer:
            first_page_text = pdf_file_buffer.pages[0].extract_text()
            
            top_details = find_top_details(first_page_text)
            
            tables = pdf_file_buffer.pages[0].extract_tables()
            table_data=find_table_details(tables)
            
            result = top_details + table_data
            pprint(result)
            result.append({'key':'file_name', 'value':pdf_file})


            file_exists = os.path.isfile('table_export_' + datetime.now().strftime('%d-%m-%y') + '.csv')

            with open('table_export_' + datetime.now().strftime('%d-%m-%y') + '.csv', 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header row if file doesn't exist
                if not file_exists:
                    writer.writerow([d['key'] for d in result])

                # Write new row
                writer.writerow([d['value'] for d in result])

            print("-----------------------")
    except Exception as e:
        print("---------------",e)