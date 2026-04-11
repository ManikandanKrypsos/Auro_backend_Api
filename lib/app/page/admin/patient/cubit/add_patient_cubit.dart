import 'package:bloc/bloc.dart';
import '../model/patient_model.dart';
import '../service/static_patient_data.dart';

part 'add_patient_state.dart';

class AddPatientCubit extends Cubit<AddPatientState> {
  AddPatientCubit() : super(const AddPatientState());

  void selectGender(String gender) =>
      emit(state.copyWith(gender: gender));

  void selectMarketingSource(String source) =>
      emit(state.copyWith(marketingSource: source));

  void selectSkinType(String type) =>
      emit(state.copyWith(skinType: type));

  Future<void> savePatient(PatientModel patient, {bool isEdit = false}) async {
    emit(state.copyWith(status: AddPatientStatus.loading));
    try {
      // Simulate network delay
      await Future.delayed(const Duration(milliseconds: 800));

      if (isEdit) {
        final index = StaticPatientData.patients.indexWhere((p) => p.id == patient.id);
        if (index != -1) {
          StaticPatientData.patients[index] = patient;
        }
      } else {
        StaticPatientData.patients.insert(0, patient);
      }
      
      emit(state.copyWith(status: AddPatientStatus.success));
    } catch (e) {
      emit(state.copyWith(
        status: AddPatientStatus.error,
        errorMessage: e.toString(),
      ));
    }
  }
}
