import 'package:bloc/bloc.dart';
import '../model/patient_model.dart';
import '../service/patient_firestore_service.dart';

part 'add_patient_state.dart';

class AddPatientCubit extends Cubit<AddPatientState> {
  final PatientFirestoreService _firestoreService;

  AddPatientCubit({PatientFirestoreService? firestoreService})
      : _firestoreService = firestoreService ?? PatientFirestoreService(),
        super(const AddPatientState());

  void selectGender(String gender) =>
      emit(state.copyWith(gender: gender));

  void selectMarketingSource(String source) =>
      emit(state.copyWith(marketingSource: source));

  void selectSkinType(String type) =>
      emit(state.copyWith(skinType: type));

  Future<void> savePatient(PatientModel patient, {bool isEdit = false}) async {
    emit(state.copyWith(status: AddPatientStatus.loading));
    try {
      if (isEdit) {
        await _firestoreService.updatePatient(patient);
      } else {
        await _firestoreService.addPatient(patient);
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
