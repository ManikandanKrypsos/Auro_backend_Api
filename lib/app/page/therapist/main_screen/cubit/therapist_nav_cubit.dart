import 'package:bloc/bloc.dart';

part 'therapist_nav_state.dart';

class TherapistNavCubit extends Cubit<TherapistNavState> {
  TherapistNavCubit() : super(const TherapistNavState());

  void selectTab(TherapistTab tab) =>
      emit(TherapistNavState(activeTab: tab));
}
