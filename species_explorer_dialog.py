# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SpeciesExplorerDialog
                                 A QGIS plugin
 Quickly fetch and visualise species occurrence data.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-06-22
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Kartoza
        email                : tim@kartoza.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QVariant

from qgis.core import QgsMessageLog  # NOQA
from qgis.core import (
    QgsField,
    QgsVectorLayer,
    QgsFeature,
    QgsPointXY,
    QgsGeometry,
    QgsProject,
    QgsCoordinateReferenceSystem)

from .occurrences import search
from .species import name_usage, name_backbone

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'species_explorer_dialog_base.ui'))


class SpeciesExplorerDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(SpeciesExplorerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.search_button.clicked.connect(self.find)
        self.fetch_button.clicked.connect(self.find)

    def find(self):
        """Search GBIF for the species provided."""
        matches = name_backbone(
            name=self.search_text.text())
        self.results_list.clear()
        for match in matches:
            QgsMessageLog.logMessage(str(match), 'SpeciesExplorer', 0)
            self.results_list.addItem(match['canonicalName'])

        species = name_usage(3329049)
        self.taxonomy_list.clear()
        # QgsMessageLog.logMessage(str(species), 'SpeciesExplorer', 0)
        self.taxonomy_list.addItem('Kingdom: %s' % species['kingdom'])
        self.taxonomy_list.addItem('Phylum: %s' % species['phylum'])
        self.taxonomy_list.addItem('Class: %s' % species['class'])
        self.taxonomy_list.addItem('Order: %s' % species['order'])
        self.taxonomy_list.addItem('Family: %s' % species['family'])
        self.taxonomy_list.addItem('Genus: %s' % species['genus'])
        self.taxonomy_list.addItem('Species: %s' % species['species'])
        self.taxonomy_list.addItem('Taxon ID: %s' % species['taxonID'])
        self.taxonomy_list.addItem('Accepted Name: %s' % species['accepted'])
        self.taxonomy_list.addItem(
            'Canonical Name: %s' % species['canonicalName'])
        self.taxonomy_list.addItem(
            'Accepted Key: %s' % species['acceptedKey'])

    def fetch(self):
        """
        Fetch Occurrence records for selected taxon.
        """
        QgsMessageLog.logMessage('Fetching occurrences', 'SpeciesExplorer', 0)
        species = name_usage(3329049)
        result = search(taxonKey=species['acceptedKey'])
        records = result['results']

        layer = QgsVectorLayer('Point', species['canonicalName'], 'memory')
        layer.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
        provider = layer.dataProvider()
        layer.startEditing()

        id_field = QgsField()
        id_field.setName('id')
        id_field.setType(QVariant.Int)
        id_field.setPrecision(0)
        id_field.setLength(10)

        layer.addAttribute(id_field)

        for record in records:
            if 'decimalLongitude' not in record or \
                            'decimalLatitude' not in record:
                continue
            try:
                feature = QgsFeature()
                feature.setGeometry(
                    QgsGeometry.fromPointXY(QgsPointXY(
                        record['decimalLongitude'], record['decimalLatitude']
                    )))
                feature.setAttributes([0, QVariant(record['identifier'])])
                provider.addFeatures([feature])
            except:
                continue

        layer.commitChanges()
        QgsProject.instance().addMapLayer(layer)