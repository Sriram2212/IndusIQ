"""
Generate Sample Industrial PDFs for Knowledge Graph Testing
============================================================
Creates multiple ready-to-use PDF documents that align perfectly with
the standalone_kg_pipeline.py entity/relationship schema.

Supported Entity Labels:
    Equipment, Component, Technician, Sensor, Issue,
    Material, Process, Location, Action, Parameter

Supported Relationship Types:
    HAS_COMPONENT, HAS_ISSUE, INSPECTED_BY, LOCATED_AT,
    CONNECTED_TO, MONITORS, REPLACED, USES, OPERATED_BY, CAUSED_BY

Run:  .venv\\Scripts\\python generate_sample_pdfs.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT_DIR = "sample_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def heading_style(size=14, bold=True, color=colors.HexColor("#1a237e")):
    return ParagraphStyle(
        "heading", fontSize=size, leading=size + 4,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        textColor=color, spaceAfter=6, spaceBefore=10
    )


def body_style(size=10):
    return ParagraphStyle(
        "body", fontSize=size, leading=14,
        fontName="Helvetica", textColor=colors.black,
        spaceAfter=4, alignment=TA_JUSTIFY
    )


def sub_style(size=9, italic=False):
    return ParagraphStyle(
        "sub", fontSize=size, leading=13,
        fontName="Helvetica-Oblique" if italic else "Helvetica",
        textColor=colors.HexColor("#444444"), spaceAfter=3
    )

def make_table(data, col_widths=None):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#e8eaf6")]),
        ('FONTNAME',   (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 1), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor("#9fa8da")),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


# ─────────────────────────────────────────────────────────────────────
# PDF 1: Pump Station Maintenance Report
# ─────────────────────────────────────────────────────────────────────
def create_pump_maintenance_report():
    path = os.path.join(OUTPUT_DIR, "pump_maintenance_report.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2.5*cm, rightMargin=2.5*cm)
    story = []
    H1 = heading_style(16)
    H2 = heading_style(12)
    B  = body_style()
    S  = sub_style()

    story.append(Paragraph("KRISHNA PETROCHEMICALS PVT. LTD.", heading_style(14, color=colors.HexColor("#b71c1c"))))
    story.append(Paragraph("Visakhapatnam Refinery — Zone 4 (Crude Distillation Unit)", sub_style(10)))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a237e")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("PUMP STATION MAINTENANCE & INSPECTION REPORT", H1))

    meta = [
        ["Report No.", "KPL-MNT-2026-08831", "Date", "22-Aug-2026"],
        ["Equipment Tag", "PMP-CDU4-P101A", "Shift", "C Shift (22:00–06:00)"],
        ["Equipment Type", "Centrifugal Pump (Main Feed)", "Work Order", "WO-2026-204417"],
        ["Manufacturer", "Grundfos Industries", "Model", "NB-100-250/220"],
        ["Installed On", "14-Feb-2019", "Serial No.", "GFI-88712-VZK"],
        ["Inspector", "M. Suresh (Sr. Instrument Tech)", "Emp ID", "EMP-10234"],
        ["Supervisor", "P. Lakshmi, Plant Reliability Eng.", "Approval Date", "23-Aug-2026"],
    ]
    story.append(make_table(meta, col_widths=[4*cm, 7*cm, 3.5*cm, 5*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("1. Equipment Overview & History", H2))
    story.append(Paragraph(
        "Pump PMP-CDU4-P101A is the primary crude feed pump serving the No. 4 Crude Distillation Unit (CDU-4) at "
        "Visakhapatnam Refinery. The pump handles crude oil at 65 degrees C with a rated flow of 320 m3/h at 7.2 bar "
        "differential pressure. It has logged 31,200 operating hours since commissioning. The mechanical seal assembly "
        "(Model: John Crane Type 8B1) was last replaced in January 2025 (WO-2025-119042) following a seal face leak "
        "that caused minor product loss. Vibration trending on the drive-end bearing has shown a gradual upward trend "
        "over the last two months (from 2.1 to 3.8 mm/s RMS). A cavitation event was reported by operator S. Patel on "
        "15-Aug-2026 during the evening shift, lasting approximately 12 minutes before suction conditions stabilised.", B))

    story.append(Paragraph("2. Inspection Findings — Sensor & Parameter Readings", H2))
    findings = [
        ["Parameter / Sensor", "Tag ID", "Measured", "Normal Range", "Status"],
        ["Vibration - Drive End Bearing", "VT-P101A-DE", "3.8 mm/s RMS", "≤ 3.5", "Marginal"],
        ["Vibration - Non-Drive End Bearing", "VT-P101A-NDE", "1.9 mm/s RMS", "≤ 3.5", "Normal"],
        ["Bearing Temperature - DE", "TT-P101A-BRG1", "72 °C", "≤ 80 °C", "Normal"],
        ["Suction Pressure", "PT-P101A-SUC", "1.82 bar", "1.8 – 2.2 bar", "Normal"],
        ["Discharge Pressure", "PT-P101A-DIS", "9.06 bar", "8.9 – 9.5 bar", "Normal"],
        ["Seal Chamber Pressure", "PT-P101A-SL", "4.4 bar", "4.0 – 5.0 bar", "Normal"],
        ["Motor Current Draw", "CT-P101A-MOT", "48.2 A", "42 – 52 A", "Normal"],
        ["Flow Rate", "FT-CDU4-FEED", "298 m3/h", "290 – 330 m3/h", "Normal"],
        ["Noise Level (1 m distance)", "—", "86 dBA", "≤ 82 dBA", "Above Limit"],
        ["Lube Oil Pressure", "PT-P101A-OIL", "2.1 bar", "2.0 – 2.5 bar", "Normal"],
    ]
    story.append(make_table(findings, col_widths=[5.5*cm, 3.5*cm, 2.8*cm, 3.2*cm, 2.5*cm]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("3. Component-Level Inspection", H2))
    comps = [
        ["Component", "Condition", "Action Taken"],
        ["Mechanical Seal (John Crane 8B1)", "Satisfactory — no leakage detected", "None"],
        ["Drive End Bearing (SKF 6314-2RS)", "Marginal vibration — trending upward", "Grease topped up; monitor weekly"],
        ["Non-Drive End Bearing (SKF 6311)", "Normal", "None"],
        ["Impeller", "Not opened — scheduled borescope pending", "WO raised: WO-2026-205001"],
        ["Suction Strainer", "Partially blocked — 18% open area loss", "Cleaned in-situ; pressure drop OK"],
        ["Coupling (Rexnord Thomas Disc)", "Good alignment — 0.04 mm offset", "None"],
        ["Gland Packing / Seal Housing", "Normal — slight moisture on gland, acceptable", "Monitored; no action"],
        ["Motor (ABB M3BP-225SM)", "Normal — no abnormal heat detected", "None"],
        ["Baseplate Anchor Bolts", "All bolts torqued to spec", "None"],
    ]
    story.append(make_table(comps, col_widths=[6*cm, 6.5*cm, 5*cm]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4. Lubrication & Materials Used", H2))
    story.append(Paragraph(
        "Bearing lubrication topped up with Mobil SHC Polyrex EM (NLGI Grade 2 polyurea grease). Quantity: 35 grams "
        "per bearing cavity. Seal flush fluid is clean condensate (conductivity < 5 microS/cm) supplied from the "
        "CDU-4 overhead condensate drum. No process oil detected in seal fluid sample taken on this date.", B))

    story.append(Paragraph("5. Root Cause — Cavitation Event (15-Aug-2026)", H2))
    story.append(Paragraph(
        "Investigation by technician M. Suresh and process engineer V. Reddy concluded that the cavitation event on "
        "15-Aug-2026 was caused by a temporary drop in suction header pressure below 1.7 bar due to the concurrent "
        "startup of PMP-CDU4-P102B (the standby pump) on the same suction header without adequate sequencing. The "
        "event lasted 12 minutes and is believed to have caused minor impeller surface erosion. A borescope inspection "
        "is recommended within 30 days to assess impeller condition.", B))

    story.append(Paragraph("6. Recommended Follow-up Actions", H2))
    actions = [
        ["#", "Action", "Priority", "Target Date", "Owner"],
        ["1", "Borescope impeller inspection (WO-2026-205001)", "High", "15-Sep-2026", "M. Suresh / Reliability"],
        ["2", "Repeat vibration trending — DE Bearing weekly", "Medium", "Ongoing", "Condition Monitoring"],
        ["3", "Review pump startup sequencing procedure SOP-OPS-0044", "Medium", "30-Aug-2026", "V. Reddy (Process)"],
        ["4", "Replace DE Bearing if vibration exceeds 4.5 mm/s", "Conditional", "On trigger", "Maintenance"],
        ["5", "Update CMMS equipment history with this inspection", "Routine", "25-Aug-2026", "M. Suresh"],
    ]
    story.append(make_table(actions, col_widths=[0.8*cm, 7*cm, 2.5*cm, 3*cm, 4.2*cm]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("7. Cross-References", H2))
    refs = [
        ["Record Type", "System", "Reference ID"],
        ["P&ID Drawing", "Eng. Document Vault", "PID-CDU4-FEED-007, Rev. D"],
        ["Prior Work Order (seal replacement)", "CMMS (SAP PM)", "WO-2025-119042"],
        ["Cavitation Event Report", "Shift Handover App", "EVT-2026-0815-CDU4"],
        ["OEM Pump Manual", "Doc Management", "OEM-GFI-NB100250-R3"],
        ["LOTO Procedure", "SOP Repository", "SOP-SAF-0021"],
    ]
    story.append(make_table(refs, col_widths=[5*cm, 5*cm, 7.5*cm]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "SYNTHETIC DOCUMENT — For Knowledge Graph testing purposes only. "
        "All names, IDs, and figures are fictitious.", sub_style(8, italic=True)))

    doc.build(story)
    print(f"[OK] Created: {path}")
    return path


# ─────────────────────────────────────────────────────────────────────
# PDF 2: Compressor Health & Predictive Maintenance Report
# ─────────────────────────────────────────────────────────────────────
def create_compressor_report():
    path = os.path.join(OUTPUT_DIR, "compressor_health_report.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2.5*cm, rightMargin=2.5*cm)
    story = []
    H1 = heading_style(16)
    H2 = heading_style(12)
    B  = body_style()
    S  = sub_style()

    story.append(Paragraph("SOUTHERN GAS CORPORATION", heading_style(14, color=colors.HexColor("#1b5e20"))))
    story.append(Paragraph("Cuddalore Gas Processing Plant — Compression Train 3", sub_style(10)))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1b5e20")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("RECIPROCATING COMPRESSOR — HEALTH & PREDICTIVE MAINTENANCE REPORT", H1))

    meta = [
        ["Report No.", "SGC-PM-2026-00345", "Date", "05-Sep-2026"],
        ["Equipment Tag", "K-301A", "Train", "Compression Train 3"],
        ["Equipment Type", "Reciprocating Compressor (2-Stage)", "Work Order", "WO-2026-301188"],
        ["Manufacturer", "Dresser-Rand", "Model", "HHE-VG / 2-Stage"],
        ["Installed On", "03-Jun-2014", "Running Hours", "68,400 hrs"],
        ["Inspector", "T. Krishnamurthy (Lead Mech. Tech)", "Emp ID", "EMP-20891"],
        ["Process Engineer", "Dr. A. Balasubramanian", "Approval Date", "06-Sep-2026"],
    ]
    story.append(make_table(meta, col_widths=[4*cm, 7*cm, 3.5*cm, 5*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("1. Equipment Description & Process Context", H2))
    story.append(Paragraph(
        "Compressor K-301A is a two-stage reciprocating compressor serving the gas sweetening section of the "
        "Cuddalore Gas Processing Plant. It compresses treated natural gas from 12 bar suction to 72 bar discharge "
        "at a design throughput of 180,000 Nm3/day. The machine is driven by an Siemens 1LG6-357 induction motor "
        "(2,200 kW, 11 kV) through a direct coupling. Piston rings on Stage 1 cylinders were last replaced during the "
        "2024 annual turnaround (TA-2024). Stage 2 suction valve assemblies showed early leakage signatures in the "
        "Q2-2026 thermal imaging survey (TI-SGC-2026-Q2-018).", B))

    story.append(Paragraph("2. Predictive Maintenance Sensor Data", H2))
    sensors = [
        ["Sensor / Parameter", "Tag", "Current Value", "Alarm Limit", "Status"],
        ["Stage 1 Suction Pressure", "PT-K301A-S1S", "12.4 bar", "11.5 – 13.0 bar", "Normal"],
        ["Stage 1 Discharge Pressure", "PT-K301A-S1D", "32.1 bar", "30 – 34 bar", "Normal"],
        ["Stage 2 Suction Pressure", "PT-K301A-S2S", "31.6 bar", "30 – 34 bar", "Normal"],
        ["Stage 2 Discharge Pressure", "PT-K301A-S2D", "70.4 bar", "68 – 74 bar", "Normal"],
        ["Interstage Gas Temperature", "TT-K301A-INT", "98 °C", "≤ 105 °C", "Normal"],
        ["Final Discharge Temperature", "TT-K301A-DIS", "112 °C", "≤ 115 °C", "Marginal"],
        ["Crankshaft Vibration X-axis", "VT-K301A-CRK-X", "4.2 mm/s", "≤ 4.0 mm/s", "Above Alarm"],
        ["Crankshaft Vibration Y-axis", "VT-K301A-CRK-Y", "2.8 mm/s", "≤ 4.0 mm/s", "Normal"],
        ["Stage 2 Valve Temperature (IR)", "TT-K301A-VLV-S2", "127 °C", "≤ 120 °C", "Above Alarm"],
        ["Lube Oil Pressure", "PT-K301A-OIL", "2.8 bar", "2.5 – 3.5 bar", "Normal"],
        ["Lube Oil Temperature", "TT-K301A-OIL", "61 °C", "≤ 70 °C", "Normal"],
        ["Motor Winding Temperature", "TT-MOT-K301A", "88 °C", "≤ 95 °C", "Normal"],
        ["Rod Drop — Cylinder 1", "RD-K301A-C1", "0.38 mm", "≤ 0.50 mm", "Normal"],
        ["Rod Drop — Cylinder 3", "RD-K301A-C3", "0.48 mm", "≤ 0.50 mm", "Marginal"],
    ]
    story.append(make_table(sensors, col_widths=[5*cm, 3.5*cm, 2.8*cm, 3.2*cm, 2.5*cm]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("3. Issues Identified", H2))
    story.append(Paragraph(
        "Three issues require attention based on current readings and trend analysis:", B))
    story.append(Paragraph(
        "<b>Issue 1 — Stage 2 Suction Valve Leakage (K301A-VLV-S2):</b> Thermal imaging and high valve temperature "
        "(127 deg C vs. 120 deg C alarm) confirm Stage 2 suction valve assembly is leaking. This is consistent with "
        "the Q2-2026 survey findings. Leaking valves reduce volumetric efficiency and increase discharge temperature. "
        "Valve replacement is recommended at next planned maintenance window.", B))
    story.append(Paragraph(
        "<b>Issue 2 — Crankshaft Vibration (X-axis above alarm):</b> Vibration of 4.2 mm/s on the crankshaft X-axis "
        "exceeds the 4.0 mm/s alarm level. Root cause is likely related to connecting rod bearing wear on cylinder 1 "
        "given the marginal rod drop reading (0.48 mm). A spectrographic oil analysis was collected and sent to lab "
        "(LAB-OIL-2026-0844).", B))
    story.append(Paragraph(
        "<b>Issue 3 — Cylinder 3 Rod Drop Trending (Marginal):</b> Rod drop on cylinder 3 is 0.48 mm against a limit "
        "of 0.50 mm. This indicates piston rider band wear. If not addressed by the next turnaround, unplanned "
        "shutdown risk increases significantly.", B))

    story.append(Paragraph("4. Materials & Lubrication", H2))
    story.append(Paragraph(
        "Cylinder lubrication uses Petro-Canada Purity FG Compressor Oil ISO VG 100 (food-grade). Crankcase uses "
        "Shell Tellus S4 ME 46 hydraulic oil (ISO VG 46). Piston rings (Stage 1) are PTFE-filled carbon grade from "
        "Hoerbiger. Stage 2 suction and discharge valves are Hoerbiger RINO plate valves.", B))

    story.append(Paragraph("5. Technician Field Notes", H2))
    story.append(Paragraph(
        '"Compressor was inspected during a 2-hour planned window. Audible higher-frequency tone near Stage 2 head '
        'confirms the valve condition we saw in the thermal survey. Rod drop on C3 is very close to the limit — I '
        'would not delay the rider band inspection beyond this TA cycle. The crankshaft vibration spike is new since '
        'last month; watching it closely. Lube oil looks clean, colour normal, no metallic sheen visible in the drain '
        'sample — lab results will confirm. Motor and coupling are fine."'
        "  — T. Krishnamurthy, Lead Mech. Tech", B))

    story.append(Paragraph("6. Recommended Actions", H2))
    actions = [
        ["#", "Action", "Priority", "Target Date", "Owner"],
        ["1", "Replace Stage 2 suction valve assembly (K301A-VLV-S2)", "High", "Next planned window", "T. Krishnamurthy"],
        ["2", "Review lube oil spectrographic results (LAB-OIL-2026-0844)", "Medium", "12-Sep-2026", "Reliability Team"],
        ["3", "Inspect connecting rod bearing — Cylinder 1 during TA", "High", "TA-2026 (Oct)", "Lead Technician"],
        ["4", "Schedule rider band replacement — Cylinder 3 in TA", "High", "TA-2026 (Oct)", "T. Krishnamurthy"],
        ["5", "Weekly vibration trending on crankshaft until TA", "Medium", "Ongoing", "Condition Monitoring"],
    ]
    story.append(make_table(actions, col_widths=[0.8*cm, 7*cm, 2.5*cm, 3*cm, 4.2*cm]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "SYNTHETIC DOCUMENT — For Knowledge Graph testing purposes only. All entities are fictitious.",
        sub_style(8, italic=True)))

    doc.build(story)
    print(f"[OK] Created: {path}")
    return path


# ─────────────────────────────────────────────────────────────────────
# PDF 3: Electrical Transformer Inspection Report
# ─────────────────────────────────────────────────────────────────────
def create_transformer_report():
    path = os.path.join(OUTPUT_DIR, "transformer_inspection_report.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2.5*cm, rightMargin=2.5*cm)
    story = []
    H1 = heading_style(16)
    H2 = heading_style(12)
    B  = body_style()
    S  = sub_style()

    story.append(Paragraph("TAMILNADU POWER GRID CORPORATION", heading_style(14, color=colors.HexColor("#4a148c"))))
    story.append(Paragraph("Tirunelveli Sub-Station — Bay 7 (132/33 kV Grid Transformer)", sub_style(10)))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4a148c")))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("POWER TRANSFORMER — ANNUAL ELECTRICAL INSPECTION REPORT", H1))

    meta = [
        ["Report No.", "TNPGC-ELEC-2026-0712", "Date", "10-Sep-2026"],
        ["Asset Tag", "TX-BAY7-132KV", "Location", "Tirunelveli Sub-Station, Bay 7"],
        ["Equipment Type", "Power Transformer 132/33 kV, 50 MVA", "Work Order", "WO-2026-TX712"],
        ["Manufacturer", "BHEL (Bhopal)", "Year of Manufacture", "2011"],
        ["Vector Group", "YNd11", "Cooling Type", "ONAN / ONAF"],
        ["Inspector", "K. Anburaj (Sr. Electrical Engineer)", "Emp ID", "EMP-40218"],
        ["Next Inspection Due", "Sep-2027", "Approval", "Chief Engineer R. Balaji"],
    ]
    story.append(make_table(meta, col_widths=[4.5*cm, 6.5*cm, 3.5*cm, 5*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("1. Transformer Overview", H2))
    story.append(Paragraph(
        "Transformer TX-BAY7-132KV is a 50 MVA, 132/33 kV oil-immersed power transformer serving as the primary "
        "grid infeed for Tirunelveli industrial zone. The unit has been in continuous service since commissioning in "
        "March 2012 and has accumulated 14 years of service. The last major internal inspection (DGA and oil "
        "processing) was conducted in September 2022. Cooling fans CF-TX7-01 through CF-TX7-04 are installed for "
        "ONAF operation. The on-load tap changer (OLTC) is a Maschinenfabrik Reinhausen (MR) VACUTAP VV model with "
        "17 tap positions, last maintained in April 2025.", B))

    story.append(Paragraph("2. Oil Analysis (Dissolved Gas Analysis — DGA)", H2))
    oil = [
        ["Gas", "Measured (ppm)", "IEEE C57.104 Limit", "Status"],
        ["Hydrogen (H2)", "85", "< 100", "Normal"],
        ["Methane (CH4)", "52", "< 120", "Normal"],
        ["Ethane (C2H6)", "41", "< 65", "Normal"],
        ["Ethylene (C2H4)", "31", "< 50", "Normal"],
        ["Acetylene (C2H2)", "8", "< 3 (alarm)", "Above Alarm"],
        ["Carbon Monoxide (CO)", "320", "< 350", "Normal"],
        ["Carbon Dioxide (CO2)", "2,840", "< 2,500 (caution)", "Above Caution"],
        ["TDCG (Total Dissolved Combustible Gas)", "537", "< 720 (Level 1)", "Normal"],
    ]
    story.append(make_table(oil, col_widths=[5.5*cm, 3.5*cm, 4.5*cm, 3*cm]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "ATTENTION: Acetylene (C2H2) at 8 ppm exceeds the IEEE C57.104 alarm threshold of 3 ppm. Acetylene "
        "generation indicates arcing or high-temperature hot spots. This finding requires follow-up with a more "
        "frequent DGA sampling at 1-month intervals and possible internal inspection.", B))

    story.append(Paragraph("3. Electrical Test Results", H2))
    elec = [
        ["Test", "Value Measured", "Acceptance Criteria", "Status"],
        ["Insulation Resistance (HV-LV) 5000V", "12,400 MΩ", "> 1,000 MΩ", "Normal"],
        ["Insulation Resistance (HV-Earth)", "9,800 MΩ", "> 1,000 MΩ", "Normal"],
        ["Polarisation Index (10-min/1-min)", "1.89", "> 1.5", "Normal"],
        ["Tan Delta (Dielectric Loss)", "0.0042", "< 0.005 at 90°C", "Normal"],
        ["Winding Resistance (HV Phase A)", "1.42 Ω", "Within ±2% of factory", "Normal"],
        ["Winding Resistance (LV Phase B)", "0.041 Ω", "Within ±2% of factory", "Normal"],
        ["OLTC Contact Resistance", "188 µΩ", "< 200 µΩ", "Normal"],
        ["Turns Ratio (Tap 9, rated)", "4.000:1", "Expected 4.000:1", "Normal"],
        ["Partial Discharge (at 1.1 pu)", "18 pC", "< 100 pC", "Normal"],
        ["Oil BDV (Breakdown Voltage)", "38 kV", "> 30 kV (IEC 60156)", "Normal"],
        ["Oil Water Content", "18 ppm", "< 25 ppm", "Normal"],
        ["Acidity of Oil", "0.09 mg KOH/g", "< 0.15 mg KOH/g", "Normal"],
    ]
    story.append(make_table(elec, col_widths=[6*cm, 3.5*cm, 4.5*cm, 2.5*cm]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4. Physical Inspection", H2))
    phys = [
        ["Component", "Condition", "Action"],
        ["Conservator Tank", "No sludge, silica gel breather 60% saturated (blue to pink)", "Replace silica gel cartridge"],
        ["Buchholz Relay", "Tested and functional; gas pocket free", "None"],
        ["Pressure Relief Device", "Sealed and intact", "None"],
        ["HV Bushings (3 units)", "Clean, no tracking marks, IR scan normal", "None"],
        ["LV Bushings (3 units)", "Hairline crack on Phase-B LV bushing shed", "Monitor; plan replacement"],
        ["Cooling Fans (CF-TX7-01 to 04)", "All fans operational; CF-TX7-03 slightly noisier than others", "Inspect CF-TX7-03 bearing"],
        ["OLTC (MR VACUTAP VV)", "Oil level OK; contacts normal; selector switch smooth", "None"],
        ["Surge Arresters (HV side)", "All 3 units healthy — IR thermography normal", "None"],
        ["Oil Level Indicator", "Normal — 68% level", "None"],
        ["Control Cabinet", "All relays and meters functional; insulation of control cables OK", "None"],
        ["Grounding / Earthing", "Earth resistance 0.8 Ω — within spec (< 1 Ω)", "None"],
    ]
    story.append(make_table(phys, col_widths=[5.5*cm, 6*cm, 6*cm]))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5. Summary of Issues & Recommendations", H2))
    actions = [
        ["#", "Issue / Action", "Priority", "Target Date", "Owner"],
        ["1", "Increase DGA sampling to monthly — Acetylene monitoring (C2H2 > 3 ppm)", "High", "Oct-2026", "K. Anburaj"],
        ["2", "Replace silica gel cartridge on conservator breather", "Medium", "25-Sep-2026", "Field Maintenance"],
        ["3", "Plan LV Phase-B bushing replacement at next outage", "Medium", "Apr-2027", "Switchgear Team"],
        ["4", "Inspect bearing on cooling fan CF-TX7-03", "Low", "30-Sep-2026", "Field Maintenance"],
        ["5", "Internal inspection (core/winding) if C2H2 continues rising", "Conditional", "On trigger", "Chief Engineer"],
    ]
    story.append(make_table(actions, col_widths=[0.8*cm, 7.5*cm, 2.5*cm, 2.8*cm, 3.9*cm]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "SYNTHETIC DOCUMENT — For Knowledge Graph testing purposes only. All entities are fictitious.",
        sub_style(8, italic=True)))

    doc.build(story)
    print(f"[OK] Created: {path}")
    return path


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  GENERATING SAMPLE INDUSTRIAL PDFs")
    print("=" * 60)
    try:
        from reportlab.lib.pagesizes import A4
    except ImportError:
        print("[ERROR] reportlab is not installed.")
        print("Run:  .venv\\Scripts\\pip install reportlab")
        exit(1)

    paths = []
    paths.append(create_pump_maintenance_report())
    paths.append(create_compressor_report())
    paths.append(create_transformer_report())

    print()
    print("=" * 60)
    print(f"  Done! {len(paths)} PDF files created in: {os.path.abspath(OUTPUT_DIR)}/")
    print()
    print("  Now run the KG pipeline on each PDF:")
    print()
    for p in paths:
        print(f"    .venv\\Scripts\\python standalone_kg_pipeline.py {p}")
    print("=" * 60)
