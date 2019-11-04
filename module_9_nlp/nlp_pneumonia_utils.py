import os, glob
import zipfile
import codecs
import sklearn.metrics
import pandas as pd
import pyConTextNLP
from pyConTextNLP import pyConTextGraph
from radnlp.data import classrslts
import radnlp.view as rview
from IPython.display import display, HTML, Image
from pyConTextNLP import itemData
from nltk import word_tokenize, sent_tokenize



# this class encapsulates all data related to a span (text sequence) annotation
# including the text it "covers" and the type (i.e. "concept") of the annotation
class Annotation(object):
    def __init__(self):
        self.start_index = -1
        self.end_index = -1
        self.type = ''
        self.spanned_text = ''

    # adding this so that pyConText's HTML markup can work seamlessly
    def getSpan(self):
        return (self.start_index, self.end_index)

    def getCategory(self):
        # pyConText graph objects actually expect a list here
        return [self.type]


# this class encapsulates all data for a document which has been annotated_doc_map
# this includes the original text, its annotations and also
class AnnotatedDocument(object):
    def __init__(self):
        self.text = ''
        self.annotations = []
        # NOTE : This "positive_label" relates to positive/possible cases of pneumonia
        self.positive_label = -1


def read_brat_annotations(lines):
    annotations = []
    # BRAT FORMAT is:
    # NUMBER[TAB]TYPE[SPACE]START_INDEX[SPACE]END_INDEX[SPACE]SPANNED_TEXT
    for line in lines:
        line = str(line)
        tab_tokens = line.split('\t')
        space_tokens = tab_tokens[1].split()
        anno = Annotation()
        anno.spanned_text = tab_tokens[-1]
        anno.type = space_tokens[0]
        anno.start_index = int(space_tokens[1])
        anno.end_index = int(space_tokens[2])
        annotations.append(anno)
    return annotations


def read_annotations(directory):
    annotated_doc_map = read_doc_annotations(directory)

    return list(annotated_doc_map.values())


def read_doc_annotations(directory):
    print('Reading annotations from directory : ' + directory)
    annotated_doc_map = {}

    filenames = os.listdir(directory)
    for name in filenames:
        if name.endswith('.txt') or name.endswith('.ann'):
            basename = name.split('.')[0]
            if basename not in annotated_doc_map:
                annotated_doc_map[basename] = AnnotatedDocument()
            anno_doc = annotated_doc_map[basename]
            # handle text and BRAT annotation files (.ann) differently
            if name.endswith('.txt'):
                with open(os.path.join(directory, name), 'rb') as f1:
                    anno_doc.text = f1.read().decode('utf8')
            else:
                with open(os.path.join(directory, name), 'rb') as f1:
                    # handle this as utf8 or we get back byte arrays
                    anno_doc.annotations = read_brat_annotations(codecs.iterdecode(f1, 'utf8'))

    # now let's finally assign a 0 or 1 to each document based on whether we see our expected type for the pneumonia label
    for key, anno_doc in annotated_doc_map.items():
        annos = anno_doc.annotations
        anno_doc.positive_label = 0
        for anno in annos:
            # NOTE : This "positive_label" relates to positive/possible cases of pneumonia
            if anno.type == 'PNEUMONIA_DOC_YES':
                anno_doc.positive_label = 1

    return annotated_doc_map

def annotated_doc_map_to_df(annotated_doc_map):
    dicts = []
    for i, (doc_id, doc) in enumerate(annotated_doc_map.items()):
        annotations = doc.annotations
        for anno in annotations:
            d = dict(anno.__dict__)
            d['document_name'] = doc_id
            d['document_idx'] = i
            d['annotation_level'] = 'document' if 'DOC' in d['type'] else 'mention'
            dicts.append(d)
    df = pd.DataFrame(dicts, columns=['document_idx', 'document_name', 'start_index', 'end_index', 'type', 'annotation_level', 'spanned_text'])
    df = df.sort_values(['document_idx', 'document_name', 'start_index', 'type']).reset_index()
    return df


def calculate_prediction_metrics(gold_docs, prediction_function):
    gold_labels = [x.positive_label for x in gold_docs]
    pred_labels = []
    for gold_doc in gold_docs:
        pred_label = prediction_function(gold_doc.text)
        pred_labels.append(pred_label)

    # now let's use scikit-learn to compute some metrics
    precision = sklearn.metrics.precision_score(gold_labels, pred_labels)
    recall = sklearn.metrics.recall_score(gold_labels, pred_labels)
    f1 = sklearn.metrics.f1_score(gold_labels, pred_labels)
    # let's use Pandas to make a confusion matrix for us
    confusion_matrix_df = pd.crosstab(pd.Series(gold_labels, name='Actual'),
                                      pd.Series(pred_labels, name='Predicted'))

    print('Precision : {0}'.format(precision))
    print('Recall :    {0}'.format(recall))
    print('F1:         {0}'.format(f1))

    print('\nConfusion Matrix : ')
    display(confusion_matrix_df)


def __insert_color_custom(txt, s, c):
    """insert HTML span style into txt. The span will change the color of the
    text located between s[0] and s[1]:
    txt: txt to be modified
    s: span of where to insert tag
    c: color to set the span to"""
    return txt[:s[0]] + '<span style="font-weight: bold;color: {0};">'.format(c) + \
           txt[s[0]:s[1]] + '</span>' + txt[s[1]:]


# helper functions to highlight annotations from BRAT
def mark_text(txt, nodes, colors={"name": "red", "pet": "blue"}, default_color="black"):
    # this function had to be copied and modified from pyConTextNLP.display.html.mark_text
    # so that the default_color could be passed through
    if not nodes:
        return txt
    else:
        n = nodes.pop(-1)
        return mark_text(__insert_color(txt,
                                        n.getSpan(),
                                        colors.get(n.getCategory()[0], default_color)),
                         nodes,
                         colors=colors,
                         # this was not being passed through
                         default_color=default_color)


# helper functions to highlight annotations from BRAT
def mark_text_custom(txt, nodes, colors={"name": "red", "pet": "blue"}, default_color="black"):
    # this function had to be copied and modified from pyConTextNLP.display.html.mark_text
    # so that the default_color could be passed through
    if not nodes:
        return txt
    else:
        n = nodes.pop(-1)
        return mark_text_custom(__insert_color_custom(txt,
                                                      n.getSpan(),
                                                      colors.get(n.getCategory()[0], default_color)),
                                nodes,
                                colors=colors,
                                # this was not being passed through
                                default_color=default_color)


def pneumonia_annotation_html_markup(anno_doc):
    from pyConTextNLP.display.html import __sort_by_span
    # this bit mimics 'mark_document_with_html' from pyConTextNLP.display.html
    colors = {}
    colors['DOCUMENT_PNEUMONIA_YES'] = 'red'
    colors['DOCUMENT_PNEUMONIA_NO'] = 'green'
    colors['SPAN_POSITIVE_PNEUMONIA_EVIDENCE'] = 'red'
    default_color = 'red'
    html = """<p> {0} </p>""".format(" ".join([mark_text_custom(anno_doc.text,
                                                                __sort_by_span(anno_doc.annotations),
                                                                colors=colors,
                                                                default_color=default_color)]))
    return html


def mark_document_with_html(doc, colors={"name": "red", "pet": "blue"}, default_color="black"):
    """takes a ConTextDocument object and returns an HTML paragraph with marked phrases in the
    object highlighted with the colors coded in colors

    doc: ConTextDocument
    colors: dictionary keyed by ConText category with values valid HTML colors

    """
    from pyConTextNLP.display.html import __sort_by_span
    from pyConTextNLP.utils import get_document_markups
    report_html = """<p> {0} </p>""".format(" ".join([mark_text_custom(m.graph['__txt'],
                                                                __sort_by_span(m.nodes()),
                                                                colors=colors,
                                                                default_color=default_color) for m in
                                               get_document_markups(doc)]))
    return report_html.replace('\n', '<br>')


def clearPyConTextRegularExpressions():
    if len(pyConTextGraph.compiledRegExprs) > 0:
        print('Clearing pyConText compiled regular expressions')
        pyConTextGraph.compiledRegExprs = {}


def view_single_sentence_graph(sentence, modifiers, targets):
    context = markup_context_document(sentence, modifiers, targets)
    class_result = classrslts(context_document=context, exam_type="Chest X-Ray", report_text=sentence,
                              classification_result='N/A')
    rview.markup_to_pydot(class_result)
    display(Image("tmp.png"))
    print(sentence)


class DocumentClassifier(object):
    def __init__(self, ruleFile, debug=False, modifiers=None, targets=None, expected_value=None):
        self.rules = {}
        self.rules_ele_list = {}
        self.conclusions = []
        self.debug = debug
        self.modifiers = modifiers
        self.targets = targets
        self.save_markups = False
        self.expected_value = expected_value
        if ruleFile is not None:
            if ruleFile.endswith('.csv') or ruleFile.endswith('.tsv') or ruleFile.endswith('.txt'):
                f = open(os.path.join(os.getcwd(), ruleFile), 'r')
                rows = f.readlines()
            else:
                rows = ruleFile.split('\n')
        else:
            print('DocumentClassifier can only take rules in string or in csv, tsv or txt file')

        if modifiers is not None and targets is not None:
            if isinstance(modifiers, str) and isinstance(targets, str):
                if (modifiers.endswith('.csv') or modifiers.endswith('.tsv') or modifiers.endswith('.txt')) \
                        and (targets.endswith('.csv') or targets.endswith('.tsv') or targets.endswith('.txt')):
                    self.setModifiersTargetsFromFiles(modifiers, targets)
            else:
                self.setModifiersTargets(modifiers, targets)

        priority = 0
        for row in rows:
            row = row.strip()
            if len(row) == 0:
                continue
            if row.startswith('#'):
                continue
            cells = row.split('\t')
            if len(cells) == 1:
                self.default_conclusion = cells[0]
                continue
            conclusion = cells[0]
            annotation_type = cells[1]
            if annotation_type not in self.rules:
                self.rules[annotation_type] = []
            rules = self.rules[annotation_type]
            rules.append(priority)

            self.rules_ele_list[priority] = set(cells[2:])
            self.conclusions.append(conclusion)
            priority += 1

    def setModifiersTargets(self, modifiers, targets):
        self.modifiers = modifiers
        self.targets = targets

    def setModifiersTargetsFromFiles(self, modifiers_file, targets_file):
        self.modifiers = pyConTextNLP.itemData.instantiateFromCSVtoitemData(os.path.join(os.getcwd(), modifiers_file))
        self.targets = pyConTextNLP.itemData.instantiateFromCSVtoitemData(os.path.join(os.getcwd(), targets_file))

    def checkMatch(self, annotation_type, modifiers, current_conclusions):
        if annotation_type not in self.rules:
            return
        current_priority = -1
        for priority in self.rules[annotation_type]:
            if len(self.rules_ele_list[priority]) == 0:
                if len(modifiers) == 0:
                    if annotation_type not in current_conclusions or current_conclusions[annotation_type] > priority:
                        current_conclusions[annotation_type] = priority
                        current_priority = priority
            elif self.rules_ele_list[priority].issubset(modifiers):
                if annotation_type not in current_conclusions or current_conclusions[annotation_type] > priority:
                    current_conclusions[annotation_type] = priority
                    current_priority = priority
                break;
        if self.expected_value is not None and self.conclusions[current_priority] in self.expected_value:
            return True
        return False

    def reset_saved_predictions(self):
        self.saved_markups_map = {}
        self.save_markups = True
        self.expected_value = None

    def predict(self, doc, expected_value={'indicate_pneumonia'}, doc_name=None):
        if self.save_markups:
            self.expected_value = expected_value
        conclusions = self.classify_doc(doc, None, doc_name)
        if expected_value.issubset(conclusions):
            return 1
        return 0

    def classify_doc(self, doc, debug=None, doc_name=None):
        if debug is None:
            debug = self.debug
        if self.modifiers is None or self.targets is None:
            print('DocumentClassifier\'s "modifiers" and/or "targets" has not been set yet.\n' +
                  'Use function: setModifiersTargets(modifiers, targets) or setModifiersTargetsFromFiles(modifiers_file,' + 'targets_file) to set them up.')
        markups = markup_context_document(doc, self.modifiers, self.targets)
        if doc_name is not None and self.save_markups and len(markups.getDocumentGraph().nodes()) > 0:
            self.saved_markups_map[doc_name] = markups
        return self.classify_markups(markups, debug, doc_name)

    def classify_markups(self, markups, debug=None, doc_name=None):
        if debug is None:
            debug = self.debug
        current_conclusions = {}
        annotation_id_modifiers = {}
        annotation_id_type = {}
        nodes_on_edge = set()
        target_id_nodes = {}
        if debug:
            annotation_id_phrase = {}
        # regroup  modifiers by each annotation
        for e in markups.getDocumentGraph().edges():
            annotation_id = e[1].getTagID()
            target_id_nodes[annotation_id] = e[1]
            nodes_on_edge.add(annotation_id)
            annotation_type = e[1].getCategory()[0]
            modifier = e[0].getCategory()[0]
            nodes_on_edge.add(e[0].getTagID())
            if annotation_id not in annotation_id_modifiers:
                annotation_id_modifiers[annotation_id] = set()
            annotation_id_modifiers[annotation_id].add(modifier)
            annotation_id_type[annotation_id] = annotation_type
            if debug:
                annotation_id_phrase[annotation_id] = e[1].getPhrase()

        # add annotations with no modifier
        for node in markups.getDocumentGraph().nodes():
            if node.getTagID() not in nodes_on_edge:
                annotation_id = node.getTagID()
                target_id_nodes[annotation_id] = node
                annotation_id_modifiers[annotation_id] = set()
                annotation_id_type[annotation_id] = node.getCategory()[0]
                if debug:
                    annotation_id_phrase[annotation_id] = node.getPhrase()

        # update decision for each annotation and its modifiers in its id order (assume the ids are assigned based on the positions)
        for annotation_id in sorted(annotation_id_type.keys()):
            annotation_type = annotation_id_type[annotation_id]
            modifiers = annotation_id_modifiers[annotation_id]
            self.checkMatch(annotation_type, modifiers, current_conclusions)
            if debug:
                print('Based on annotation: "' + annotation_id_phrase[
                    annotation_id] + '" has type: \t"' + annotation_type + '"\twith modifiers: ' + str(modifiers))
                print('\tCurrent conclusion is:\t' + str(self.get_conclusion_set(current_conclusions)) + '\n')

        if len(current_conclusions) == 0:
            return {self.default_conclusion}
        return self.get_conclusion_set(current_conclusions)

    def get_conclusion_set(self, current_conclusions):
        conclusion = set()
        for priority in current_conclusions.values():
            conclusion.add(self.conclusions[priority])
        return conclusion


def markup_sentence(s, modifiers, targets, prune_inactive=True, verbose=False):
    """
    """
    markup = pyConTextGraph.ConTextMarkup()
    markup.setRawText(s)
    markup.cleanText()
    markup.markItems(targets, mode="target")
    markup.markItems(modifiers, mode="modifier")
    markup.pruneMarks()
    markup.dropMarks('Exclusion')
    # apply modifiers to any targets within the modifiers scope
    markup.applyModifiers()
    markup.pruneSelfModifyingRelationships()
    if prune_inactive:
        markup.dropInactiveModifiers()
    return markup


# This function now works on entire documents combining all sentence-level objects into one object we can can then graph
def markup_context_document(report_text, modifiers, targets):
    context = pyConTextGraph.ConTextDocument()

    # Split up into sentences
    sentences = tokenize_sents(report_text)
    for sentence in sentences:
        m = markup_sentence(sentence, modifiers=modifiers, targets=targets)
        context.addMarkup(m)
    
    return context

def tokenize_sents(text):
    return sent_tokenize(text)

from collections import namedtuple

classrslts = namedtuple("classrslts",
                        ["context_document",
                         "exam_type",
                         "report_text",
                         "classification_result"])

non_positive_categories = ["definite_negated_existence",
                 "probable_negated_existence",
                 "probable_existence",
                "indication"
                 ]


def classify_pneumonia_document(context, non_positive_categories, verbose=0):

    num_positive = 0
    graph = context.getDocumentGraph()
    for target in graph.getMarkedTargets():
        modified_by_non_positive = False
        for modifier in graph.getModifiers(target):
            if modifier.getCategory()[0] in non_positive_categories:
                if verbose:
                    print("--'{0}' modified by '{1}' - not positive evidence".format(target.getPhrase().upper(),
                                                                               modifier.getPhrase().upper()))
                modified_by_non_positive = True
        if modified_by_non_positive is False:
            num_positive += 1
            if verbose:
                print("--'{0}' not modified by non-positive modifiers: setting num_positive = {1}".format(target.getPhrase().upper(),
                                                                                         num_positive))
    if num_positive > 0:
        return 1 # Positive
    else:
        return 0
    
def list_errors(gold_docs, modifiers, targets, non_positive_categories, print_prediction_metrics=False):
    
    fn_docs=[]
    fp_docs=[]
    context_documents = dict()
    
    gold_labels = [x.positive_label for x in gold_docs.values()]
    pred_labels = []
    for doc_name, gold_doc in gold_docs.items():
        gold_label=gold_doc.positive_label
        context = markup_context_document(gold_doc.text, modifiers, targets)
        context_documents[doc_name] = context
        pred_label = classify_pneumonia_document(context, non_positive_categories)
        pred_labels.append(pred_label)
#       Differentiate false positive and false negative error
        if gold_label==0 and pred_label==1:
            fp_docs.append(doc_name)
        elif gold_label==1 and pred_label==0:
            fn_docs.append(doc_name)
    if (print_prediction_metrics):
        precision = sklearn.metrics.precision_score(gold_labels, pred_labels)
        recall = sklearn.metrics.recall_score(gold_labels, pred_labels)
        f1 = sklearn.metrics.f1_score(gold_labels, pred_labels)
        # Let's use Pandas to make a confusion matrix for us
        confusion_matrix_df = pd.crosstab(pd.Series(gold_labels, name='Actual'),
                                          pd.Series(pred_labels, name='Predicted'))

        print('Precision : {0}'.format(precision))
        print('Recall :    {0}'.format(recall))
        print('F1:         {0}'.format(f1))

        print('\nConfusion Matrix : ')
        display(confusion_matrix_df)
        
    return fn_docs,fp_docs, context_documents
