import 'package:bloc/bloc.dart';

part 'add_patient_state.dart';



class AddPatientCubit extends Cubit<AddPatientState> {
  AddPatientCubit() : super(const AddPatientState());

  void selectGender(String gender) =>
      emit(state.copyWith(gender: gender));

  void selectMarketingSource(String source) =>
      emit(state.copyWith(marketingSource: source));

  void selectSkinType(String type) =>
      emit(state.copyWith(skinType: type));
}
