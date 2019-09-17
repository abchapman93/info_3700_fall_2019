lab_query = """
select labevents.subject_id, labevents.hadm_id as 'hospital_admission_id',
    labevents.charttime as 'datetime',
    labevents.value, labevents.flag,
    labevents.valueuom as 'units',
    d_labitems.test_name,
    d_labitems.fluid,
    d_labitems.category,
    d_labitems.loinc_code,
    d_labitems.loinc_description
from labevents
    inner join d_labitems
    on labevents.itemid = d_labitems.itemid
"""

chart_events_query = """
select
	chartevents.subject_id, chartevents.icustay_id,
    chartevents.charttime, chartevents.value1,
    chartevents.stopped,
    d_chartitems.label
 from mimic2.chartevents
inner join d_chartitems on chartevents.itemid = d_chartitems.itemid
"""

icd9_query = """
select subject_id, hadm_id as 'hospital_admission_id',
    code as 'icd9_code', description as 'icd9_code_description'
from icd9
"""

med_query = """
select
medevents.subject_id, medevents.icustay_id,
    medevents.charttime, medevents.realtime,
    medevents.volume, medevents.dose,
    medevents.doseuom, medevents.solvolume,
    medevents.solunits, medevents.route,
    medevents.stopped,
    d_meditems.label as 'medication_label'

from mimic2.medevents     -- patient, dosage, annotation
    inner join d_meditems      --
        on (medevents.itemid = d_meditems.itemid)

    inner join a_meddurations
        on (medevents.subject_id = a_meddurations.subject_id
            and medevents.icustay_id = a_meddurations.icustay_id
            and d_meditems.itemid = a_meddurations.itemid
            and medevents.elemid = a_meddurations.elemid
            and medevents.cuid = a_meddurations.cuid
            )
"""

text_query = """
select
	subject_id, hadm_id as 'hospital_admission_id',
    icustay_id,
    charttime,
    correction,
    category as 'note_type',
    title as 'note_title',
	text
from mimic2.noteevents
"""

demographic_query = """
select
	subject_id,
    hadm_id as 'hospital_admission_id',
    marital_status_descr as 'marital_status',
    ethnicity_descr as 'ethnicity',
    overall_payor_group_descr as 'insurance',
    religion_descr as 'religion',
    admission_type_descr as 'admission_type'
from demographic_detail
"""
