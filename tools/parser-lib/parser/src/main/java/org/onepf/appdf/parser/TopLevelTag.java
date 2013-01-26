package org.onepf.appdf.parser;

import org.onepf.appdf.model.Application;
import org.w3c.dom.Node;

public enum TopLevelTag implements NodeParser<Application> {

	CATEGORIZATION{

		@Override
		public void parse(Node node, Application application) throws ParsingException {	
			(new CategorizationParser()).parse(node, application);
		}
		
	},
	DESCRIPTION{

		@Override
		public void parse(Node node, Application application) throws ParsingException {
			(new DescriptionParser(true)).parse(node, application);			
		}
		
	},
	DESCRIPTION_LOCALIZATION{
	    @Override
        public void parse(Node node, Application application) throws ParsingException {
            (new DescriptionParser(false)).parse(node, application);         
        }
        
	}
	;		
}