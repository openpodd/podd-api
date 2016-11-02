# -*- encoding: utf-8 -*-

import datetime
import os, shutil
import random

from django.conf import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.test import TestCase

from accounts.models import User
from common import factory
from reports.models import AdministrationArea


class TestSearchNearByArea(TestCase):
    def setUp(self):
        self.area1 = factory.create_administration_area(name='Seoul', location='POINT (100.552206 13.808277)')
        self.area1_1 = self.area1.add_child(name='Gangname', location=self.area1.location)
        self.area2 = factory.create_administration_area(name='Tokyo', location='POINT (139.5792387 35.7388576)')
        self.area2_1 = self.area2.add_child(name='Odiba', location=self.area2.location)
        self.area2_2 = self.area2.add_child(name='Akihabara', location=self.area2.location)
        self.area3 = factory.create_administration_area(name='London', location='POINT (-0.1015987 51.5286416)')
        self.area3_1 = self.area3.add_child(name='Stamford', location=self.area3.location)
        self.area3_2 = self.area3.add_child(name='Wembley', location=self.area3.location)

    def test_access_search_nearby_area(self):
        response = self.client.get(reverse('search_nearby_area'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'area/search_nearby_area.html')

    def test_access_search_nearby_area_with_no_query_context(self):
        response = self.client.get(reverse('search_nearby_area'))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(len(response.context['areas']), 0)
        self.assertEqual(response.context['query'], None)

    def test_access_search_nearby_area_with_same_query_context(self):
        params = {
            'query': 'Central park',
        }
        response = self.client.get(reverse('search_nearby_area'), params)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(len(response.context['areas']), 0)
        self.assertEqual(response.context['query'], 'Central park')

    def test_access_search_nearby_area_with_all_query_context_and_the_number_of_areas_less_than_10(self):
        params = {
            'query': 'Central park',
            'lat': 40.782865,
            'log': -73.965355,
        }
        response = self.client.get(reverse('search_nearby_area'), params)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(len(response.context['areas']), 5)
        self.assertEqual(response.context['query'], 'Central park')
        self.assertTrue(response.context['areas'][0]['distance'] - response.context['areas'][1]['distance'] <= 0)
        self.assertTrue(response.context['areas'][1]['distance'] - response.context['areas'][2]['distance'] <= 0)
        self.assertTrue(response.context['areas'][2]['distance'] - response.context['areas'][3]['distance'] <= 0)
        self.assertTrue(response.context['areas'][3]['distance'] - response.context['areas'][4]['distance'] <= 0)

    def test_access_search_nearby_area_with_all_query_context_and_the_number_of_areas_more_than_10(self):
        factory.create_administration_area(name='New York', location='POINT (-73.979681 40.7033121)')
        factory.create_administration_area(name='San Francisco', location='POINT (-122.4376 37.7577)')
        factory.create_administration_area(name='Hongkok', location='POINT (114.041282 22.312967)')
        factory.create_administration_area(name='Bangkok', location='POINT (100.6331108 13.7246005)')
        factory.create_administration_area(name='Chiang Mai', location='POINT (98.9564772 18.771752)')
        factory.create_administration_area(name='Melbourne', location='POINT (145.079616 -37.8602828)')
        factory.create_administration_area(name='Sydney', location='POINT (150.9224326 -33.7969235)')
        params = {
            'query': 'Central park',
            'lat': 40.782865,
            'log': -73.965355,
        }
        response = self.client.get(reverse('search_nearby_area'), params)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(len(response.context['areas']), 10)
        self.assertEqual(response.context['query'], 'Central park')
        self.assertTrue(response.context['areas'][0]['distance'] - response.context['areas'][1]['distance'] <= 0)
        self.assertTrue(response.context['areas'][1]['distance'] - response.context['areas'][2]['distance'] <= 0)
        self.assertTrue(response.context['areas'][2]['distance'] - response.context['areas'][3]['distance'] <= 0)
        self.assertTrue(response.context['areas'][3]['distance'] - response.context['areas'][4]['distance'] <= 0)
        self.assertTrue(response.context['areas'][4]['distance'] - response.context['areas'][5]['distance'] <= 0)
        self.assertTrue(response.context['areas'][5]['distance'] - response.context['areas'][6]['distance'] <= 0)
        self.assertTrue(response.context['areas'][6]['distance'] - response.context['areas'][7]['distance'] <= 0)
        self.assertTrue(response.context['areas'][7]['distance'] - response.context['areas'][8]['distance'] <= 0)
        self.assertTrue(response.context['areas'][8]['distance'] - response.context['areas'][9]['distance'] <= 0)
