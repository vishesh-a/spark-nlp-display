import random
import os
import json
from . import style_utils as style_config
from IPython.display import display, HTML

here = os.path.abspath(os.path.dirname(__file__))

class EntityResolverOutput:
    def __init__(self):
        with open(os.path.join(here, 'label_colors/ner.json'), 'r', encoding='utf-8') as f_:
            self.label_colors = json.load(f_)

    #public function to get color for a label
    def getLabelColor(self, label):
        """Returns color of a particular label
        
        Input: entity label <string>
        Output: Color <string> or <None> if not found
        """

        if str(label).lower() in self.label_colors:
            return self.label_colors[label.lower()]
        else:
            return None

    # private function for colors for display
    def __getLabel(self, label):
        """Set label colors.
        
        Input: dictionary of entity labels and corresponding colors
        Output: self object - to allow chaining
        Note: Previous values of colors will be overwritten
        """
        if str(label).lower() in self.label_colors:
            return self.label_colors[label.lower()]
        else:
            #update it to fetch from git new labels 
            r = lambda: random.randint(100,255)
            return '#%02X%02X%02X' % (r(), r(), r())

    def setLabelColors(self, color_dict):
        """Sets label colors.

        input: dictionary of entity labels and corresponding colors
        output: self object - to allow chaining
        note: Previous values of colors will be overwritten
        """

        for key, value in color_dict.items():
          self.label_colors[key.lower()] = value
        return self      

    def __verifyStructure(self, result, label_col, document_col, original_text):

        if original_text is None:
            basic_msg_1 = """Incorrect annotation structure of '{}'.""".format(document_col)
            if not hasattr(result[document_col][0], 'result'):
                raise AttributeError(basic_msg_1+""" 'result' attribute not found in the annotation. 
                Make sure '"""+document_col+"""' is a list of objects having the following structure: 
                    Annotation(type='annotation', begin=0, end=10, result='This is a text')
                Or You can pass the text manually using 'raw_text' argument.""")

        basic_msg_1 = """Incorrect annotation structure of '{}'.""".format(label_col)
        basic_msg = """
        In sparknlp please use 'LightPipeline.fullAnnotate' for LightPipeline or 'Pipeline.transform' for PipelineModel.
        Or 
        Make sure '"""+label_col+"""' is a list of objects having the following structure: 
            Annotation(type='annotation', begin=0, end=0, result='Adam', metadata={'entity': 'PERSON'})"""

        for entity in result[label_col]:
            if not hasattr(entity, 'begin'):
                raise AttributeError( basic_msg_1 + """ 'begin' attribute not found in the annotation."""+basic_msg)
            if not hasattr(entity, 'end'):
                raise AttributeError(basic_msg_1 + """ 'end' attribute not found in the annotation."""+basic_msg)
            if not hasattr(entity, 'result'):
                raise AttributeError(basic_msg_1 + """ 'result' attribute not found in the annotation."""+basic_msg)
            if not hasattr(entity, 'metadata'):
                raise AttributeError(basic_msg_1 + """ 'metadata' attribute not found in the annotation."""+basic_msg)
            if 'entity' not in entity.metadata:
                raise AttributeError(basic_msg_1+""" KeyError: 'entity' not found in metadata."""+basic_msg)

    def __verifyInput(self, result, label_col, document_col, original_text):
        # check if label colum in result
        if label_col not in result:
            raise AttributeError("""column/key '{}' not found in the provided dataframe/dictionary.
            Please specify the correct key/column using 'label_col' argument.""".format(label_col))
        
        if original_text is not None:
            # check if provided text is correct data type
            if not isinstance(original_text, str):
                raise ValueError("Invalid value for argument 'raw_text' input. Text should be of type 'str'.")
        
        else:
            # check if document column in result
            if document_col not in result:
                raise AttributeError("""column/key '{}' not found in the provided dataframe/dictionary.
                Please specify the correct key/column using 'document_col' argument.
                Or You can pass the text manually using 'raw_text' argument""".format(document_col))

        self.__verifyStructure( result, label_col, document_col, original_text)

    # main display function
    def __displayNer(self, result, label_col, resolution_col, document_col, original_text, labels_list = None):

        if original_text is None:
            original_text = result[document_col][0].result

        if labels_list is not None:
            labels_list = [v.lower() for v in labels_list]
        label_color = {}
        html_output = ""
        pos = 0
        for entity, resol in zip(result[label_col], result[resolution_col]):
            entity_type = entity.metadata['entity'].lower()
            if (entity_type not in label_color) and ((labels_list is None) or (entity_type in labels_list)) :
                label_color[entity_type] = self.__getLabel(entity_type)

            begin = int(entity.begin)
            end = int(entity.end)
            if pos < begin and pos < len(original_text):
                white_text = original_text[pos:begin]
                html_output += '<span class="others" style="background-color: white">{}</span>'.format(white_text)
            pos = end+1

            if entity_type in label_color:
                html_output += '<span class="entity-wrapper" style="background-color: {}"><span class="entity-name">{} </span><span class="entity-type">{}</span><span class="entity-name" style="background-color: {}">{} </span><span class="entity-name" style="background-color: {}">{}</span></span>'.format(
                    label_color[entity_type],
                    entity.result,
                    entity.metadata['entity'],
                    '#D2C8C6' , resol.result,
                    '#DDD2D0', resol.metadata['resolved_text'])

            else:
                html_output += '<span class="others" style="background-color: white">{}</span>'.format(entity.result)

        if pos < len(original_text):
            html_output += '<span class="others" style="background-color: white">{}</span>'.format(original_text[pos:])

        html_output += """</div>"""

        html_output = html_output.replace("\n", "<br>")

        return html_output

    def display(self, result, label_col, resolution_col, document_col='document', raw_text=None):
        """Displays NER visualization. 

        Inputs:
        result -- A Dataframe or dictionary.
        label_col -- Name of the column/key containing NER annotations.
        document_col -- Name of the column/key containing text document.
        original_text -- Original text of type 'str'. If specified, it will take precedence over 'document_col' and will be used as the reference text for display.
        labels_list -- A list of labels that should be highlighted in the output. Default: Display all labels.

        Output: Visualization
        """
        
        #self.__verifyInput(result, label_col, document_col, raw_text)
        
        html_content = self.__displayNer(result, label_col, resolution_col, document_col, raw_text)
        
        return display(HTML(style_config.STYLE_CONFIG+ " "+html_content))
