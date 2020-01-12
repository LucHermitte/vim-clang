#include <cstddef>
namespace  NS1
{
struct S {
    void f(int i, float);
    void g(double d) const;
    void h(double d) volatile; // cannot detect volatile...
    constexpr auto i(double d = 12.5) { return 42 * d;}

    virtual int pure() = 0;
    virtual int v();

    template <typename T, std::size_t N = 50>
    void t(
            T element,
            unsigned u,
            double const& d,
            int & i);

    S() noexcept = default;
    void wi() noexcept(true);
    void wi2() noexcept(false);
    void wi3() noexcept;

    void f(int) = delete;

    explicit S(double);
    S(int);
    ~S();
    S(S const&);
    S& operator=(S const&);
    S& operator=(S &&) = delete;
};

constexpr bool Toto = false;
struct S0 {
    S0() = delete;
    virtual int v(double d);
    virtual int v_pub_pri();
    virtual int pure() = 0;
private:
    /**
     * Sample doc.
     * @param[in] s  bla
     *
     * @return bli
     * @throw None if `Toto`
     */
    virtual int constone(S const& s) const noexcept(Toto);
    virtual int constone2(S const& s) const noexcept(Toto) = 0;
};

struct S2 : S0 {
    int v(double d) override {
        return 42;
    }
private:
    int v_pub_pri() override;
    int pure() final;
public:
    class C {
        C() = default;
        static void f();

        bool doWeCanAnInfiniteLoop(C const& brother);
    };
};

template <typename T, std::size_t N = 50>
struct S3 : S2, private S2::C
{
    void reset() ;
    T array[N] = {};
};

template <typename T, int N = 50> struct array {
    void f() {
        int i;
    }
    T tab[N];
};
} // namespace NS1

void g(double d);
