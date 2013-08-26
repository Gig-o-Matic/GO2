# Utilities for graph-o-matic

from gig import *
from band import *
import debug

def get_band_and_gig(band_id, gig_id):

        # which band are we talking about?
        if band_id is None:
            debug_print('get_band_and_gig: no band id passed in!')
            return (None, None) # todo figure out what to do if there's no ID passed in

        # find the gig we're interested in
        if gig_id is None:
            debug_print('get_band_and_gig: no gig id passed in!')
            return (None, None) # todo figure out what to do if there's no ID passed in

        band=get_band_from_id(band_id) # todo more efficient if we include the band key?
        
        if band is None:
            debug_print('get_band_and_gig: did not find a band!')
            return (None, None) # todo figure out what to do if there's no ID passed in

            
        gig=get_gig_from_id(band, gig_id) # todo more efficient if we include the band key?
        
        if gig is None:
            debug_print('get_band_and_gig: did not find a gig!')
            return (None, None) # todo figure out what to do if there's no ID passed in

        return (band, gig)