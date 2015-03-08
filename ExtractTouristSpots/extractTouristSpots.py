__author__ = 'dexter'

import argparse
from googleplaces import GooglePlaces, types
from suffix_tree import SuffixTree
from pytrie import SortedStringTrie as Trie
from nltk.tokenize import RegexpTokenizer

googlePlacesApiKey="AIzaSyCXzGg8gQPwo97Zxx3Hy3g-Vdh9_zq46qM"
google_places = GooglePlaces(googlePlacesApiKey)

def getTouristSpots(city):
    '''
    Use both text-search and nearby search from Google Places API to get a list of Tourist attractions
    in a particular city
    '''
    from geopy.geocoders import Nominatim
    geolocator = Nominatim()
    cityLocation = geolocator.geocode(city)
    print cityLocation.address
    print cityLocation.latitude, cityLocation.longitude
    queryText = 'tourist attractions in ' + city
    locationType=[types.TYPE_AMUSEMENT_PARK, types.TYPE_ART_GALLERY, types.TYPE_CASINO, types.TYPE_CHURCH,
              types.TYPE_HINDU_TEMPLE, types.TYPE_MOSQUE, types.TYPE_MUSEUM, types.TYPE_NATURAL_FEATURE,
              types.TYPE_PARK, types.TYPE_PLACE_OF_WORSHIP, types.TYPE_SYNAGOGUE, types.TYPE_ZOO, types.TYPE_POINT_OF_INTEREST]

    queryResult = google_places.text_search(query=queryText,
                                            location=city,
                                            types=locationType)

    touristSpots = set()
    for spot in queryResult.places:
        touristSpots.add(spot.name.upper())

    # To make our nearby search more relevant and accurate, use the exact coordinates of city in question
    queryResult = google_places.nearby_search(location=cityLocation.address,
                                              lat_lng={'lat': cityLocation.latitude, 'lng':cityLocation.longitude},
                                              keyword=['tourist'],
                                              radius=20000)

    for spot in queryResult.places:
        #print spot.name
        touristSpots.add(spot.name.upper())

    return frozenset(touristSpots)

class TouristSpotFinder:

    def __init__(self):
        self.touristSpots = dict()

    def updateTouristSpotDatabase(self, cities):
        for city in cities:
            touristSpotsOfCity = getTouristSpots(city)
            # Create a Trie from all the tourist spots of the city
            trie = Trie()
            for spot in touristSpotsOfCity:
                # Insert uppercase name for consistency
                trie.__setitem__(spot.upper(), 0)
            # Put the trie in the dictionary
            self.touristSpots[city] = trie

    def identifyTouristSpots(self, tokens, travelPlanSuffixTree):

        touristSpots = set()
        for token in tokens:
            #print "Checking for " + token
            for city in self.touristSpots.keys():
                # Get the trie for this city
                trie = self.touristSpots[city]
                # If the trie has at least one key prefixed by token
                if trie.keys(prefix=token):
                    for key in trie.keys(prefix=token):
                        # Discard tourist spots that don't exist in the original Travel Plan
                        idx = travelPlanSuffixTree.find_substring(key)
                        if (idx >= 0):
                            touristSpots.add(key)
        return frozenset(touristSpots)

class TravelPlan:
    def __init__(self, travelPlanFile):
        # Parse and Sanitize TravelPlan as String
        text = ''
        with open(travelPlanFile, 'r') as f:
            text = f.read().replace('\n',' ').upper()

        tokenizer = RegexpTokenizer(r'\w+')
        self.tokens = tokenizer.tokenize(text.upper())
        self.travelPlanSuffixTree = SuffixTree(text)

    def getTokens(self):
        return self.tokens

    def getTravelPlanSuffixTree(self):
        return self.travelPlanSuffixTree


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c","--cities", help="Comma separated list of cities relevant to the Travel Plan")
    parser.add_argument("-f", "--planFile", help = "File holding the travel plan")
    args = parser.parse_args()
    touristSpotFinder = TouristSpotFinder()

    cities = args.cities.split(',')
    touristSpotFinder.updateTouristSpotDatabase(cities)
    travelPlan = TravelPlan(args.planFile)
    spots = touristSpotFinder.identifyTouristSpots(travelPlan.getTokens(), travelPlan.getTravelPlanSuffixTree())

    print "============================================================="
    print " Tourist Spots Identified in " + args.cities + " Travel Plan"
    print "============================================================="
    for spot in spots:
        print spot

if __name__ == '__main__':
    main()
