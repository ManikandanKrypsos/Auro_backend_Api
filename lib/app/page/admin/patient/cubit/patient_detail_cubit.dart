import 'package:bloc/bloc.dart';

part 'patient_detail_state.dart';

class PatientDetailCubit extends Cubit<PatientDetailState> {
  PatientDetailCubit() : super(PatientDetailState(selectedTab: 0));
    void selectTab(int index) => emit(state.copyWith(selectedTab: index));
}
