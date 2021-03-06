# -*- coding: utf-8 -*-

# Copyright © 2015, Miguel Madrid Mencía and Daniel Arnao Rodríguez. All rights reserved.
#
# Developed by:
#
# Miguel Madrid Mencía and Daniel Arnao Rodríguez
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# “Software”), to deal with the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimers.
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimers in the
# documentation and/or other materials provided with the distribution.
# Neither the names of Miguel Madrid Mencía and Daniel Arnao Rodríguez,
# nor the names of its contributors may be used to endorse or promote
# products derived from this Software without specific prior written
# permission.  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH THE
# SOFTWARE.

import os
import cv2
import numpy
import args_processor

'''
Algoritmo de visión computerizada para la medición del espesor de la coroides 
mediante la distancia fovea en tomografías de coherencia optica de la lámina cribosa
para la automatización del seguimiento de la uveitis.
Paso 0: Extracción de la zona ROI de la imagen
Paso 1: Corrección de la inclinación de la imagen
Paso 2: Obtención de la fovea (mínimo de la curva)
Paso 3: Trazar la vertical que pase por dicho punto 
        y marcar la intersección con el resto de membranas
Paso 4: Hallar la distancia buscada
'''


class Algorithm:
    def __init__(self, image_name, step_mode):

        self.img_file = cv2.imread(image_name)
        self.roi = self.img_file
        self.steps_counter = 0
        self.iteration_number = 0
        self.step_mode = step_mode
        self.image_name = image_name
        self.img_original = None
        self.img_gray_original = None
        self.img_horizontal = None
        self.img_gray_horizontal = None
        self.img_fovea_point = None
        self.img_membranes = None
        self.fovea_point = (0, 0)
        self.first_point_coroides = (0, 0)
        self.second_point_coroides = (0, 0)
        # self.micras_por_pixel = 200/33.0
        # self.micras_por_pixel = 6
        self.micras_por_pixel = 200 / 50.0
        # self.micras_por_pixel = 4.0
        self.step_zero = False
        self.step_one = False
        self.step_two = False
        self.step_three = False

    def to_roi(self):
        self.step_zero = True
        first_point = (0, 0)
        second_aux_point = (0, 0)
        gray = cv2.cvtColor(self.roi, cv2.COLOR_BGR2GRAY)
        ret, otsu_threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        dilation = cv2.dilate(otsu_threshold, numpy.ones((15, 15), numpy.uint8), iterations=2)
        if step_mode:
            img_line = self.roi.copy()
            cv2.line(img_line, (int(round(1.25 * self.roi.shape[1] / 3)), 0),
                     (int(round(1.25 * self.roi.shape[1] / 3)), img_line.shape[0]), (0, 0, 255), 1)
            self.save_step(img_line, 'roi_rang_first_point')
        self.save_step(otsu_threshold, 'roi_otsu_first_point')
        self.save_step(dilation, 'roi_otsu_dilation')
        # Punto de arriba a la izquierda del área de trabajo
        for i in xrange(int(round(1.25 * self.roi.shape[1] / 3)), 0, -1):
            if dilation[50, i] != 0:
                first_point = (i, 50)
                break

        if self.step_mode:
            img_point = self.roi.copy()
            cv2.circle(img_point, first_point, 2, (0, 0, 255), 4)
            self.save_step(img_point, 'roi_first_point')

        # Punto de abajo a la izquierda del área de trabajo (auxiliar, hay que disminuirlo)
        for i in xrange(self.roi.shape[0] - 1, 0, -1):
            if dilation[i, first_point[0]] != 0:
                second_aux_point = (first_point[0], i)
                break

        ret, binary_threshold = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        if self.step_mode:
            self.save_step(binary_threshold, 'roi_binary_first_point')
            img_point = self.roi.copy()
            cv2.circle(img_point, second_aux_point, 2, (0, 0, 255), 4)
            self.save_step(img_point, 'roi_second_aux_point')

        first_aux_middle_point = (0, 0)
        for i in xrange(second_aux_point[1], 0, -1):
            if binary_threshold[i, 2 * binary_threshold.shape[1] / 4] != 0:
                first_aux_middle_point = (2 * binary_threshold.shape[1] / 4, i)
                break

        second_aux_middle_point = (0, 0)
        for i in xrange(second_aux_point[1], 0, -1):
            if binary_threshold[i, 3 * binary_threshold.shape[1] / 4] != 0:
                second_aux_middle_point = (3 * binary_threshold.shape[1] / 4, i)
                break

        # Punto de abajo a la izquierda definitivo
        second_point = (
            second_aux_point[0],
            first_aux_middle_point[1] + (first_aux_middle_point[1] - second_aux_middle_point[1]))
        # cv2.circle(img, second_point, 1, (0, 0, 255), 3)
        # Punto de abajo a la derecha
        third_point = (binary_threshold.shape[1],
                       second_aux_middle_point[1] + (second_aux_middle_point[1] - first_aux_middle_point[1]))
        if self.step_mode:
            img_first_point = self.roi.copy()
            img_line = self.roi.copy()
            cv2.line(img_line, (second_aux_point[0], second_aux_point[1]),
                     (img_line.shape[1], second_aux_point[1]),
                     (255, 0, 0), 1)
            self.save_step(img_line, 'roi_botton_lower_line')
            cv2.circle(img_first_point, first_aux_middle_point, 2, (0, 255, 0), 4)
            self.save_step(img_first_point, 'roi_first_aux_middle_point')
            img_second_point = self.roi.copy()
            cv2.circle(img_second_point, second_aux_middle_point, 2, (0, 255, 0), 4)
            self.save_step(img_second_point, 'roi_second_aux_middle_point')
            cv2.circle(img_first_point, second_aux_middle_point, 2, (0, 255, 0), 4)
            self.save_step(img_first_point, 'roi_aux_middle_points')
            img_second_point = self.roi.copy()
            cv2.circle(img_second_point, second_point, 2, (0, 0, 255), 5)
            self.save_step(img_second_point, 'roi_second_point')
            img_third_point = self.roi.copy()
            cv2.circle(img_third_point, third_point, 2, (0, 0, 255), 5)
            self.save_step(img_third_point, 'roi_third_point')
            cv2.circle(img_second_point, third_point, 2, (0, 0, 255), 5)
            self.save_step(img_second_point, 'roi_points')
            cv2.circle(img_second_point, first_aux_middle_point, 2, (0, 255, 0), 4)
            cv2.circle(img_second_point, second_aux_middle_point, 2, (0, 255, 0), 4)
            self.save_step(img_second_point, 'roi_all_points')

        first_roi_point = first_point

        if second_point[1] > third_point[1]:
            second_roi_point = (self.roi.shape[1], second_point[1])
        else:
            second_roi_point = (self.roi.shape[1], third_point[1])

        if step_mode:
            img_point = self.roi.copy()
            cv2.circle(img_point, second_roi_point, 2, (0, 255, 255), 8)
            self.save_step(img_point, 'roi_final_point')
            cv2.circle(img_point, first_roi_point, 2, (0, 255, 255), 8)
            self.save_step(img_point, 'roi_final_points')
            cv2.rectangle(img_point, first_roi_point, second_roi_point, (255, 0, 255), 2)
            self.save_step(img_point, 'roi_final_rectangle')

        self.roi = self.roi[first_roi_point[1]:second_roi_point[1], first_roi_point[0]:second_roi_point[0]]
        self.img_original = self.roi.copy()
        self.img_gray_original = cv2.cvtColor(self.img_original, cv2.COLOR_BGR2GRAY)
        self.img_horizontal = self.img_original
        self.img_gray_horizontal = self.img_original
        self.img_fovea_point = self.img_original
        self.img_membranes = self.img_original

    # http://homepages.inf.ed.ac.uk/rbf/HIPR2/hough.htm
    # http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_imgproc/py_houghlines
    # /py_houghlines.html
    # https://github.com/abidrahmank/OpenCV2-Python/blob/master/Official_Tutorial_Python_Codes/3_imgproc
    # /houghlines.py
    # http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_imgproc
    # /py_geometric_transformations/py_geometric_transformations.html
    def to_horizontal(self):
        self.step_one = True
        edges_canny = cv2.Canny(self.img_gray_original, 150, 200, apertureSize=3)
        lines = cv2.HoughLines(edges_canny, 1, numpy.pi / 180, 275)
        if lines is None:
            self.img_horizontal = self.img_original
        else:
            for rho, theta in lines[0]:
                # Use the first not horizontal line as reference and rotate with that theta
                # radians to degrees (precision float error allowed < 1)
                # theta > 0 avoid vertical lines
                # 90 degrees line is horizontal, not use as reference
                if abs((theta * 180 / numpy.pi) - 90) > 1 and theta > 0:

                    # print "theta = %s\n" % (theta * 180 / numpy.pi)

                    rows, cols = self.img_gray_original.shape
                    # rotate image to the horizontal (line of reference degrees minus 90 degrees)
                    rotation = cv2.getRotationMatrix2D((cols / 2, rows / 2), (theta * 180 / numpy.pi) - 90, 1)
                    self.img_horizontal = cv2.warpAffine(self.img_original, rotation, (cols, rows))
                    if self.img_horizontal is None:
                        self.img_horizontal = self.img_original

                    if step_mode:
                        a = numpy.cos(theta)
                        b = numpy.sin(theta)
                        x0 = a * rho
                        y0 = b * rho
                        x1 = int(x0 + 1000 * (-b))
                        y1 = int(y0 + 1000 * a)
                        x2 = int(x0 - 1000 * (-b))
                        y2 = int(y0 - 1000 * a)
                        draw_line_img = self.img_original.copy()
                        edges_canny = cv2.cvtColor(edges_canny, cv2.COLOR_GRAY2BGR)
                        self.save_step(edges_canny, 'horizontal_Canny_Hough')
                        edges_canny_line = edges_canny.copy()
                        cv2.line(edges_canny_line, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.line(draw_line_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.line(edges_canny, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        self.save_step(edges_canny_line, 'horizontal_Canny_Hough_recta')
                        canny_hough = cv2.addWeighted(draw_line_img, 0.3, edges_canny, 0.7, 0)
                        self.save_step(canny_hough, 'horizontal_Canny+Hough')
                        self.save_step(draw_line_img, 'horizontal_Hough_recta')
                        horizontal_hough_img = cv2.warpAffine(draw_line_img, rotation, (cols, rows))
                        self.save_step(horizontal_hough_img, 'horizontal_Horizontal_recta')
                        self.save_step(self.img_horizontal, 'horizontal_Horizontal_final')
                    break

        self.img_gray_horizontal = cv2.cvtColor(self.img_horizontal, cv2.COLOR_BGR2GRAY)
        ret, binary_threshold = cv2.threshold(self.img_gray_horizontal, 10, 255, cv2.THRESH_BINARY)
        self.save_step(binary_threshold, 'roi_binary_horizontal')
        roi_point = (0, 0)
        for i in xrange(binary_threshold.shape[0] - 1, 0, -1):
            if binary_threshold[i, binary_threshold.shape[1] / 2] != 0:
                roi_point = (binary_threshold.shape[1] / 2, i)
                break

        if self.step_mode:
            img_point = self.img_horizontal.copy()
            cv2.circle(img_point, roi_point, 2, (0, 255, 0), 4)
            self.save_step(img_point, 'roi_point_horizontal')

        self.img_horizontal = self.img_horizontal[0:roi_point[1], 0:self.img_horizontal.shape[1]]
        self.img_gray_horizontal = cv2.cvtColor(self.img_horizontal, cv2.COLOR_BGR2GRAY)

    def calculate_fovea(self):
        self.step_two = True
        blur = cv2.medianBlur(self.img_gray_horizontal, 7)
        self.save_step(blur, 'fovea_blur')
        ret, binary_threshold = cv2.threshold(blur, 30, 255, cv2.THRESH_BINARY)
        self.save_step(binary_threshold, 'fovea_threshold')

        y, x = binary_threshold.shape

        # Hemos comprobado que el threshold en más de una ocasión crea una línea recta horizontal en la fóvea.
        # Para encontrar un punto céntrico,
        # llevaremos dos puntos de coordenadas, el de más a la izquierda y el de más a la derecha,
        # para así luego poder calcular la media en el eje x
        punto1 = (0, 0)
        punto2 = (0, 0)

        # Restringimos el área para buscar en el eje de las x
        # teniendo en cuenta que la fóvea esta siempre entre 1/3 y 2/3
        for i in xrange(x / 3, 2 * x / 3):
            for j in xrange(y):

                if binary_threshold[j, i] == 255:

                    # Actualización punto más bajo y a la derecha
                    if punto1[1] == j:
                        punto2 = (i, j)

                    # Actualización de los puntos más bajos
                    if punto1[1] < j:
                        punto1 = (i, j)
                        punto2 = (i, j)

                    break

                    # Cálculo de la media de los valores de la x de los dos puntos
        if self.step_mode:
            img_points = self.img_horizontal.copy()
            img_lines = img_points.copy()
            cv2.circle(img_points, punto1, 2, (0, 255, 0), 3)
            cv2.circle(img_points, punto2, 2, (0, 255, 0), 3)
            cv2.line(img_lines, (img_lines.shape[1] / 3, 0), (img_lines.shape[1] / 3, img_lines.shape[0]),
                     (0, 255, 255), 1)
            cv2.line(img_lines, (2 * img_lines.shape[1] / 3, 0),
                     (2 * img_lines.shape[1] / 3, img_lines.shape[0]),
                     (0, 255, 255), 1)
            self.save_step(img_lines, 'fovea_lines')
            cv2.circle(img_lines, punto1, 2, (0, 255, 0), 3)
            cv2.circle(img_lines, punto2, 2, (0, 255, 0), 3)
            self.save_step(img_lines, 'fovea_points_lines')
            self.save_step(img_points, 'fovea_points')

        x = (punto1[0] + punto2[0]) / 2
        y = punto1[1]

        self.img_fovea_point = self.img_horizontal.copy()
        self.fovea_point = (x, y)
        cv2.circle(self.img_fovea_point, self.fovea_point, 2, (0, 0, 255), 3)
        self.save_step(self.img_fovea_point, 'fovea_point')

    def membranes_detector(self):
        self.step_three = True
        self.img_membranes = self.img_horizontal.copy()

        img_first_blur = cv2.medianBlur(self.img_gray_horizontal, 9)
        self.save_step(img_first_blur, 'espesor_Blur_primer_punto')
        ret, img_first_point = cv2.threshold(img_first_blur, 179, 255, cv2.THRESH_BINARY)
        img_first_point = cv2.Canny(img_first_point, 100, 100 * 3, apertureSize=3)
        self.save_step(img_first_point, 'espesor_Canny_primer_punto')

        for i in xrange(3 * img_first_point.shape[0] / 4, self.fovea_point[1], -1):
            if img_first_point[i, self.fovea_point[0]] == 255:
                self.first_point_coroides = (self.fovea_point[0], i)
                break

        if self.step_mode:
            img_line = cv2.cvtColor(img_first_point, cv2.COLOR_GRAY2BGR)
            cv2.line(img_line, (0, 3 * img_first_point.shape[0] / 4),
                     (img_line.shape[1] - 1, 3 * img_first_point.shape[0] / 4), (0, 255, 0), 1)
            self.save_step(img_line, 'espesor_primer_punto_rango')
            img_point = cv2.cvtColor(img_first_point, cv2.COLOR_GRAY2BGR)
            cv2.circle(img_point, self.first_point_coroides, 2, (0, 0, 255), 3)
            cv2.circle(img_line, self.first_point_coroides, 2, (0, 0, 255), 3)
            self.save_step(img_line, 'espesor_primer_punto_linea')
            self.save_step(img_point, 'espesor_primer_punto_final')

        img_second_point = cv2.medianBlur(self.img_gray_horizontal, 15)
        self.save_step(img_second_point, 'espesor_medianBlur_segundo_punto')
        adaptative_threshold = cv2.adaptiveThreshold(img_second_point, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                     cv2.THRESH_BINARY, 173, 3)
        self.save_step(adaptative_threshold, 'espesor_adaptative_threshold_segundo_punto')

        # Generamos nuestro propio canny a partir de findcontours y quitar los más pequeños, el ruido
        contours, hierarchy = cv2.findContours(adaptative_threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if step_mode:
            black_img = numpy.zeros((self.img_membranes.shape[0], self.img_membranes.shape[1], 3),
                                    numpy.uint8)
            cv2.drawContours(black_img, contours, -1, (255, 255, 255), 1)
            self.save_step(black_img, 'espesor_findContours_todos_segundo_punto')
        micras = -1
        size = 4000
        while micras < 0:
            self.iteration_number += 1
            iteration = 'iteration=' + str(self.iteration_number) + '_'
            final_contours = []
            for contour in contours:
                if cv2.contourArea(contour) > size:
                    final_contours.append(contour)

            # http://stackoverflow.com/a/12890573
            black_img = numpy.zeros((self.img_membranes.shape[0], self.img_membranes.shape[1], 3),
                                    numpy.uint8)
            cv2.drawContours(black_img, final_contours, -1, (255, 255, 255), 1)
            self.save_step(black_img, iteration + 'espesor_findContours_grandes_segundo_punto')
            if self.step_mode:
                img_point = black_img.copy()
                cv2.line(img_point, (0, 6 * black_img.shape[0] / 7),
                         (black_img.shape[1] - 1, 6 * black_img.shape[0] / 7),
                         (0, 255, 0), 1)
                self.save_step(img_point, iteration + 'espesor_findContours_grandes_rango_segundo_punto')
            img_second_point = cv2.cvtColor(black_img, cv2.COLOR_BGR2GRAY)

            # detectar el punto inferior de abajo a arriba
            for i in xrange(6 * img_second_point.shape[0] / 7, self.first_point_coroides[1], -1):
                if img_second_point[i, self.fovea_point[0]] == 255:
                    self.second_point_coroides = (self.fovea_point[0], i)
                    break

            if self.step_mode:
                img_point = black_img.copy()
                cv2.circle(img_point, self.second_point_coroides, 2, (0, 0, 255), 3)
                img_line = img_point.copy()
                cv2.line(img_line, (0, 6 * black_img.shape[0] / 7),
                         (black_img.shape[1] - 1, 6 * black_img.shape[0] / 7),
                         (0, 255, 0), 1)
                self.save_step(img_line, iteration + 'espesor_segundo_punto_linea')
                self.save_step(img_point, iteration + 'espesor_segundo_punto_final')

            if self.step_mode:
                img_points = cv2.addWeighted(cv2.cvtColor(img_first_point, cv2.COLOR_GRAY2BGR), 0.5,
                                             black_img, 0.5, 0)
                cv2.circle(img_points, self.first_point_coroides, 2, (0, 0, 255), 3)
                cv2.circle(img_points, self.second_point_coroides, 2, (0, 0, 255), 3)
                self.save_step(img_points, iteration + 'espesor_findContours_grandes_ambos_puntos')

            cv2.line(self.img_membranes, (self.first_point_coroides[0], self.first_point_coroides[1]),
                     (self.second_point_coroides[0], self.second_point_coroides[1]), (0, 255, 0), 1)
            cv2.line(self.img_membranes, (self.first_point_coroides[0] - 15, self.first_point_coroides[1]),
                     (self.first_point_coroides[0] + 15, self.first_point_coroides[1]), (0, 0, 255), 1)
            cv2.line(self.img_membranes, (self.second_point_coroides[0] - 10, self.second_point_coroides[1]),
                     (self.second_point_coroides[0] + 10, self.second_point_coroides[1]), (0, 0, 255), 1)

            micras = (self.second_point_coroides[1] - self.first_point_coroides[1]) * self.micras_por_pixel
            p = (self.first_point_coroides[0] + 50,
                 (self.first_point_coroides[1] + self.second_point_coroides[1]) / 2)
            cv2.putText(self.img_membranes, str(micras), p, cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 255),
                        1,
                        cv2.CV_AA)
            if micras < 0:
                size -= 500
                self.img_membranes = self.img_horizontal.copy()
            else:
                self.save_img(self.img_membranes, iteration + 'espesor_final')

    def save_step(self, img, title):
        if step_mode:
            self.save_img(img, title)

    def save_img(self, img, title):
        if step_mode:
            self.steps_counter += 1
            cv2.imwrite(os.path.splitext(self.image_name)[0] + '_' + str(self.steps_counter) + '_' + title +
                        os.path.splitext(self.image_name)[1], img)
        else:
            cv2.imwrite(os.path.splitext(self.image_name)[0] + '_' + title +
                        os.path.splitext(self.image_name)[1], img)


def run_algorithm(img_name, step_mode):
    algorithm = Algorithm(img_name, step_mode)
    algorithm.to_roi()
    algorithm.to_horizontal()
    algorithm.calculate_fovea()
    algorithm.membranes_detector()


if __name__ == "__main__":

    args_processor.carpeta_procesada = 'PROCESADAS'
    args_processor.args = args_processor.parser.parse_args()
    step_mode = False

    start = cv2.getTickCount()
    if args_processor.args.pasos:
        step_mode = True

    if args_processor.args.archivos:
        for archivo in args_processor.args.archivos:
            args_processor.procesar_archivo(archivo, args_processor.carpeta_procesada, step_mode,
                                            run_algorithm)

    if args_processor.args.carpetas:
        for carpeta in args_processor.args.carpetas:
            os.chdir(carpeta)
            args_processor.procesar_carpeta(args_processor.carpeta_procesada, step_mode, run_algorithm)
            os.chdir('..')

    end = cv2.getTickCount()
    seconds = (end - start) / cv2.getTickFrequency()
    print 'seconds elapsed: ', seconds
