
import numpy as np
from clinica.pipeline.machine_learning import base
import os.path as path
from pandas.io import parsers
import clinica.pipeline.machine_learning.voxel_based_io as vbio
import clinica.pipeline.machine_learning.svm_utils as utils


class CAPST1Input(base.MLInput):

    def __init__(self, caps_directory, subjects_visits_tsv, diagnoses_tsv, group_id, fwhm=0, modulated="on",
                 mask_zeros=True, precomputed_kernel=None):

        self._caps_directory = caps_directory
        self._group_id = group_id
        self._fwhm = fwhm
        self._modulated = modulated
        self._mask_zeros = mask_zeros
        self._orig_shape = None
        self._data_mask = None
        self._images = None
        self._x = None
        self._y = None
        self._kernel = None

        subjects_visits = parsers.read_csv(subjects_visits_tsv, sep='\t')
        if list(subjects_visits.columns.values) != ['participant_id', 'session_id']:
            raise Exception('Subjects and visits file is not in the correct format.')
        self._subjects = list(subjects_visits.participant_id)
        self._sessions = list(subjects_visits.session_id)

        diagnoses = parsers.read_csv(diagnoses_tsv, sep='\t')
        if 'diagnosis' not in list(diagnoses.columns.values):
            raise Exception('Diagnoses file is not in the correct format.')
        self._diagnoses = list(diagnoses.diagnosis)

        if precomputed_kernel is not None:
            if type(precomputed_kernel) == np.ndarray:
                if precomputed_kernel.shape == (len(self._subjects), len(self._subjects)):
                    self._kernel = precomputed_kernel
                else:
                    raise Exception("""Precomputed kernel provided is not in the correct format.
                    It must be a numpy.ndarray object with number of rows and columns equal to the number of subjects,
                    or a filename to a numpy txt file containing an object with the described format.""")
            elif type(precomputed_kernel == str):
                self._kernel = np.loadtxt(precomputed_kernel)
            else:
                raise Exception("""Precomputed kernel provided is not in the correct format.
                It must be a numpy.ndarray object with number of rows and columns equal to the number of subjects,
                or a filename to a numpy txt file containing an object with the described format.""")

    def get_images(self):
        """

        Returns: a list of filenames

        """
        if self._images is not None:
            return self._images

        if self._fwhm == 0:
            self._images = [path.join(self._caps_directory, 'subjects', self._subjects[i], self._sessions[i],
                                      't1/spm/dartel/group-' + self._group_id,
                                      '%s_%s_T1w_segm-graymatter_space-Ixi549Space_modulated-%s_probability.nii.gz'
                                      % (self._subjects[i], self._sessions[i], self._modulated))
                            for i in range(len(self._subjects))]
        else:
            self._images = [path.join(self._caps_directory, 'subjects', self._subjects[i], self._sessions[i],
                                      't1/spm/dartel/group-' + self._group_id,
                                      '%s_%s_T1w_segm-graymatter_space-Ixi549Space_modulated-%s_fwhm-%dmm_probability.nii.gz'
                                      % (self._subjects[i], self._sessions[i], self._modulated, self._fwhm))
                            for i in range(len(self._subjects))]
        return self._images

    def get_x(self):
        """

        Returns: a numpy 2d-array.

        """
        if self._x is not None:
            return self._x

        print 'Loading ' + str(len(self.get_images())) + ' subjects'
        self._x, self._orig_shape, self._data_mask = vbio.load_data(self._images, mask=self._mask_zeros)
        print 'Subjects loaded'

        return self._x

    def get_y(self):
        """

        Returns: a list of integers. Each integer represents a class.

        """
        if self._y is not None:
            return self._y

        unique = list(set(self._diagnoses))
        self._y = np.array([unique.index(x) for x in self._diagnoses])
        return self._y

    def get_kernel(self, kernel_function=utils.gram_matrix_linear, recompute_if_exists=False):
        """

        Returns: a numpy 2d-array.

        """
        if self._kernel is not None and not recompute_if_exists:
            return self._kernel

        if self._x is None:
            self.get_x()

        print "Computing kernel ..."
        self._kernel = kernel_function(self._x)
        print "Kernel computed"
        return self._kernel

    def save_kernel(self, output_dir):
        """

        Args:
            output_dir:

        Returns:

        """
        if self._kernel is not None:
            filename = path.join(output_dir, 'kernel.txt')
            np.savetxt(filename, self._kernel)
            return filename
        raise Exception("Unable to save the kernel. Kernel must be computed before.")