import pandas as pd
import numpy as np


# import easygui


#! replace append with concat
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


# ? choose file

# GUI file picker
# report = easygui.fileopenbox()

report = "sample_report.csv"

report_data = pd.read_csv(report)
lookup = pd.read_csv("sku_replacement.csv")

#! date picker
date_start = "4/4/2020"
date_end = "4/10/2020"


# ? get all skus that are not found in lookup df
print("\nLoading Lookup Table........")

er_df = report_data.merge(lookup, how="outer", on="sku", indicator=True)

er_df = er_df[er_df["_merge"] == "left_only"]

er_df = er_df.drop_duplicates(subset="sku")

# remove G&R skus from er_df
for index, row in er_df.iterrows():
    if row["sku"].lower().startswith("amzn.gr."):
        er_df.drop(index, inplace=True)

# ? fix missing skus in lookup df


def ercheck(lookup):

    print("the following skus cannot be placed")
    print(er_df.sku)
    print("-------------------")

    new_skus = pd.DataFrame(
        {
            "sku": [],
            "qb_sku": [],
            "multiplier": [],
        }
    )

    for index, row in er_df.iterrows():
        ersku = row["sku"]
        default_multiplier = 1

        # dont try to fix amzn.gr. skus
        if ersku.lower().startswith("amzn.gr."):
            pass

        else:
            newsku = input("enter correct sku for " + ersku + " as per QB\n")
            newmultiplier = (
                input("enter product multiplier (leave blank for single packs): ")
                or default_multiplier
            )

            print("-------------------")

            print(
                "for sku " + "\x1B[1;4m" + ersku + "\x1B[0m" + " youve entered:\n"
                "New SKU: " + newsku + "\n" + "Multiplier: " + str(newmultiplier)
            )

            print("-------------------")

            # add to newskus df
            new_skus = new_skus.append(
                {"sku": ersku, "qb_sku": newsku, "multiplier": newmultiplier},
                ignore_index=True,
            )

    print(new_skus)
    confirm = input("does this look correct? (enter y/yes or n/no)\n")

    if confirm == "y":
        print("CONFIRMED!\nAdding these rows to the lookup table for next time")
        # add df of new skus to lookup.csv
        # new_skus.to_csv('sku_replacement.csv', mode='a', index=False, header=False)
        lookup = lookup.append(new_skus, ignore_index=True)
        print("--------------------")

    elif confirm == "n":
        # check for typos and try again
        print("OK lets try this again:")
        print("-------------------")
        print("---- ATTEMPT 2 ----")
        print("-------------------")
        ercheck(lookup)


print("\Fixing Incorrect SKUs........")

if len(er_df.index) == 0:
    print("---------------------")
    print("-- ALL SKUs FIXED ---")
    print("---------------------")
else:
    ercheck(lookup)


# ? get correct skus from lookup df
# gotta figure out how to also lookup from the new_skus df too
qb_merged = report_data.merge(lookup, how="left", on="sku")

print("\nFinished Fetching Correct SKUs")

# ? parse g&r skus to get proper skus
# check if any part of a sku is contained in the lookup df
print("\nParsing Grade and Resell SKUs.......")

for index, row in qb_merged.iterrows():
    # for every G&R sku in the df
    if row["sku"].lower().startswith("amzn.gr."):
        grsku = row["sku"]
        # check if its in the lookup df
        for indexl, lrow in lookup.iterrows():
            if lrow["qb_sku"].lower() in grsku.lower():
                # set qb_sku in qb_merged df to correct sku
                gsku = lookup.at[indexl, "qb_sku"]
                qb_merged.at[index, "qb_sku"] = gsku
                qb_merged.at[index, "multiplier"] = lookup.at[indexl, "multiplier"]
                print(f"    changed {grsku} to {gsku}.")
                # if its type of order change type to G&R
                if row["type"] == "Order":
                    qb_merged.at[index, "type"] = "G&R"
                    print(f"    changed {grsku} to type of G&R.")
                break


# ? multiply qty by multiplier

print("\nMultiplying Kits.......")

qb_merged["new qty"] = qb_merged["quantity"] * qb_merged["multiplier"]


# ? Handle all adjustment cases

print("Fixing Adjustments.......")

for index, row in qb_merged.iterrows():
    if row["type"] == "Fee Adjustment":
        qb_merged.at[index, "type"] = "Adjustment"
        qb_merged.at[index, "qb_sku"] = "Fee Adjustment"
        print("    Fixed Fee Adjustment.")

    elif row["type"] == "Liquidation Adjustments":
        qb_merged.at[index, "type"] = "Adjustment"
        print("    " + row["qb_sku"] + "Set to Adjustment")


# ? handle all assorted fees

print("Fixing Fees.......")

fee_types = [
    "Service Fee",
    "FBA Customer Return Fee",
    "FBA Inventory Fee",
    "Shipping",
    "Shipping Fee",
    "Shipping Services",
]

for index, row in qb_merged.iterrows():
    if row["type"] in fee_types:
        fee = row["type"]
        qb_merged.at[index, "type"] = "Fee"
        print(f"    Fixed {fee}.")


# ? set all negative adjustments as type refund

print("\nFixing Negative Adjustments.......")

for index, row in qb_merged.iterrows():
    if row["type"] == "Adjustment":
        if row["total"] < 0:
            qb_merged.at[index, "type"] = "Refund"
            print("    " + row["sku"] + " changed to Refund")

# ? set all rows with marketplace 'sim1' to 0 qty

print("\nFixing Ebay Orders.......")

for index, row in qb_merged.iterrows():
    if row["marketplace"] == "sim1.stores.amazon.com" and row["type"] == "Order":
        qb_merged.at[index, "marketplace"] = 0
        print("    " + row["qb_sku"] + "qty removed: Ebay Item.")


# ? pivot report_data on new sku, total new qty, total price

print("\nCreating Pivot Table.......")

pivot = pd.pivot_table(
    qb_merged, index=["type", "qb_sku"], values=["new qty", "total"], aggfunc=np.sum
)
pivot = pivot.reset_index()

print("\nSplitting Invoices.......")

# ? sales df

salesdf = pd.DataFrame(
    {
        "Invoice No.": [],
        "Customer": [],
        "Invoice Date": [],
        "Memo": [],
        "Product/Service": [],
        "Qty": [],
        "Amount": [],
    }
)

for index, row in pivot.iterrows():
    sku = row["qb_sku"]
    qty = row["new qty"]
    amount = row["total"]
    if row["type"] == "Order":
        salesdf = salesdf.append(
            {
                "Invoice No.": int(1001),
                "Customer": "Amazon",
                "Invoice Date": date_end,
                "Memo": f"Sales {date_start} - {date_end}",
                "Product/Service": sku,
                "Qty": int(qty),
                "Amount": amount,
            },
            ignore_index=True,
        )

print("\n\nsales:\n___________\n", salesdf)


# ? adjustments df

adjustmentsdf = pd.DataFrame(
    {
        "Invoice No.": [],
        "Customer": [],
        "Invoice Date": [],
        "Memo": [],
        "Product/Service": [],
        "Qty": [],
        "Amount": [],
    }
)

for index, row in pivot.iterrows():
    sku = row["qb_sku"]
    qty = row["new qty"]
    amount = row["total"]
    if row["type"] == "Adjustment":
        adjustmentsdf = adjustmentsdf.append(
            {
                "Invoice No.": int(1002),
                "Customer": "Amazon",
                "Invoice Date": date_end,
                "Memo": f"Adjustments {date_start} - {date_end}",
                "Product/Service": sku,
                "Qty": int(qty),
                "Amount": amount,
            },
            ignore_index=True,
        )

print("\n\nAdjustments:\n___________\n", adjustmentsdf)

# ? G&R and liquidations

grdf = pd.DataFrame(
    {
        "Invoice No.": [],
        "Customer": [],
        "Invoice Date": [],
        "Memo": [],
        "Product/Service": [],
        "Qty": [],
        "Amount": [],
    }
)

for index, row in pivot.iterrows():
    sku = row["qb_sku"]
    qty = row["new qty"]
    amount = row["total"]
    if row["type"] == "G&R" or row["type"] == "Liquidation":
        grdf = grdf.append(
            {
                "Invoice No.": int(1003),
                "Customer": "Amazon",
                "Invoice Date": date_end,
                "Memo": f"G&R + Liquidations {date_start} - {date_end}",
                "Product/Service": sku,
                "Qty": int(qty),
                "Amount": amount,
            },
            ignore_index=True,
        )

print("\n\nG&R and Liquidations:\n___________\n", grdf)

# ? refunds and fees
# see if i can upload credit memos also

refundsdf = pd.DataFrame(
    {
        "Invoice No.": [],
        "Customer": [],
        "Invoice Date": [],
        "Memo": [],
        "Product/Service": [],
        "Qty": [],
        "Amount": [],
    }
)


for index, row in pivot.iterrows():
    sku = row["qb_sku"]
    qty = row["new qty"]
    amount = row["total"]
    if row["type"] == "Refund" or row["type"] == "Fee":
        refundsdf = refundsdf.append(
            {
                "Invoice No.": int(1004),
                "Customer": "Amazon",
                "Invoice Date": date_end,
                "Memo": f"Refunds and Fees {date_start} - {date_end}",
                "Product/Service": sku,
                "Qty": int(qty),
                "Amount": amount,
            },
            ignore_index=True,
        )

print("\n\nRefunds and Fees:\n___________\n", refundsdf)


# ? print errors
ers = 0
types = ["Order", "Adjustment", "G&R", "Liquidation", "Refund", "Fee"]

for index, row in qb_merged.iterrows():
    if row["qb_sku"] == "NaN":
        sku = row["sku"]
        ers += 1
        print("{sku} is blank")

    elif row["type"] not in types:
        unknown_type = row["type"]
        ers += 1
        print(f"Unknown Type: {unknown_type}")


# ? Done Message
if ers == 0:
    print("\nExporting to Excel......\n")

    # @ salesdf.to_csv(f'sales_{date_end}.csv')
    # @ adjustmentsdf.to_csv(f'adjustments_{date_end}.csv')
    # @ grdf.to_csv(f'G&R_{date_end}.csv')
    # @ refundsdf.to_csv(f'refunds_{date_end}.csv')
    # @ print('--------------------')

    # @ print('Invoice successfully saved!')

    exit(0)
else:
    print(f"{ers} errors")
    exit(1)
